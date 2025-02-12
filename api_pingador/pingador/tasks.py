from pingador.models import Task
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .libs_conection.conections import busca_ip_cliente
from conector_pingador.pingador_dados_facil import PingService
from celery.exceptions import MaxRetriesExceededError
import logging
import json
import os
from dotenv import load_dotenv


logger = logging.getLogger(__name__)

load_dotenv()

ENDPOINT = os.environ.get('ENDPOINT')
ENDPOINT_VM = os.environ.get('ENDPOINT_VM')


@shared_task(queue='jornada_digital_queue')
def ProcessPingJornadaDigital(circuito, task_id):
    """
    Tarefa Celery para realizar teste de ping e registrar informações no banco.
    """
    logger.info(f"##### Iniciando ProcessPingJornadaDigital para o circuito {circuito} #####")

    try:        
        task = Task.objects.filter(task_id=task_id).first()
        if not task:
            raise ValueError(f"Tarefa com task_id {task_id} não encontrada.")

        task.status = "Em andamento"
        task.start_time = timezone.now()
        task.save()
        logger.info(f"Tarefa {task_id} atualizada para 'Em andamento'.")

        ping_result = {"error": "Nenhum teste de ping foi executado"}

        with transaction.atomic():
            # Verifica se existem dados recentes
            existing_task = None
            if existing_task:
                time_difference = timezone.now() - existing_task.end_time
                if time_difference <= timedelta(hours=48) and existing_task.ipv4_cliente:
                    logger.info(f"Usando dados existentes no banco para o circuito {circuito}.")
                    _atualiza_task_com_dados_existentes(task, existing_task)
                    
                    # Executa o teste de ping com os dados existentes
                    ping_service = PingService()
                    if task.produto == 'VM':
                        logger.info(f"Produto VM detectado para circuito: {circuito}. Realizando ping com circuito e localidade.")
                        ping_result = ping_service.ping(
                            endpoint=ENDPOINT_VM,
                            circuito=task.ccto,
                            localidade=task.localizacao
                        )
                    else:
                        logger.info(f"Produto CN detectado para circuito: {circuito}. Realizando ping com IPv4 do cliente.")
                        ping_result = ping_service.ping(
                            endpoint=ENDPOINT,
                            numeric_host=task.ipv4_cliente
                        )
                else:
                    existing_task = None

            # Busca dados do cliente, se necessário
            if not existing_task:
                buscar_dados = busca_ip_cliente(circuito)
                if not buscar_dados:
                    _finaliza_task_com_erro(task, f"Circuito {circuito} não possui IPV4 cadastrado")
                    return

                # Atualiza o task com os dados do cliente
                _atualiza_task_com_busca(task, buscar_dados)

                # Decide o endpoint e parâmetros para o ping

                task.ccto = buscar_dados['ccto']
                task.save()
                ping_service = PingService()
                if buscar_dados.get('produto', '').upper() == 'VM':
                    logger.info(f"Produto VM detectado para circuito: {circuito}. Realizando ping com circuito e localidade.")
                    ping_result = ping_service.ping(
                        endpoint=ENDPOINT_VM,
                        circuito=str(buscar_dados['ccto']),
                        localidade=str(buscar_dados['loc'])
                    )
                else:
                    logger.info(f"Produto CN detectado para circuito: {circuito}. Realizando ping com IPv4 do cliente.")
                    ping_result = ping_service.ping(
                        endpoint=ENDPOINT,
                        numeric_host=buscar_dados['ip_cliente']
                    )
            if "error" in ping_result:
                # Se houver erro, finalize a task com o erro específico
                _finaliza_task_com_erro(task, ping_result.get("message", "Erro desconhecido"))
            else:
                _processa_resultado_ping(task, ping_result)

        logger.info(f"##### Finalizando ProcessPingJornadaDigital para o circuito {circuito} #####")

    except MaxRetriesExceededError as e:
        logger.error(f"Máximo de tentativas excedido para o circuito {circuito}: {str(e)}")
        raise e

    except Exception as e:
        logger.exception(f"Erro ao processar tarefa para o circuito {circuito}: {str(e)}")
        if task:
            task.status = "Falha"
            task.traceback = str(e)
            task.end_time = timezone.now()
            task.save()
        raise e


def _atualiza_task_com_dados_existentes(task, existing_task):
    """
    Atualiza o task com dados existentes no banco.
    """
    
    for field in ["ipv4_cliente", "ip_backbone", "pe", "produto", "modelo_equipamento", "localizacao", "descricao"]:
        setattr(task, field, getattr(existing_task, field))
    task.save()


def _atualiza_task_com_busca(task, buscar_dados):
    """
    Atualiza o task com os dados buscados do cliente.
    """
    task.ipv4_cliente = buscar_dados['ip_cliente']
    task.ip_backbone = buscar_dados['ip_backbone']
    task.pe = buscar_dados['pe']
    task.modelo_equipamento = buscar_dados['modelo']
    task.localizacao = buscar_dados['loc']
    task.produto = buscar_dados['produto']
    task.descricao = buscar_dados['descricao']
    task.save()


def _finaliza_task_com_erro(task, mensagem_erro):
    """
    Finaliza o task com um erro específico.
    """
    logger.error(mensagem_erro)
    task.status = 'Concluido'
    task.resultado = 'error'
    task.end_time = timezone.now()
    task.traceback = mensagem_erro
    task.save()
    logger.error(mensagem_erro)


def _processa_resultado_ping(task, ping_result):
    """
    Processa o resultado do ping e atualiza o task.
    """
    logger.info("Processando resultado do ping.")
    # logger.info("Resultado do ping:\n%s", json.dumps(ping_result, indent=4, ensure_ascii=False))

    if ping_result.get("codigo_mensagem"):
        codigo = ping_result.get("codigo_mensagem")
        if codigo == "MSG700":
            mensagem_erro = ping_result.get("mensagem")
            _finaliza_task_com_erro(task, mensagem_erro)
        else:
            _finaliza_task_com_erro(task, mensagem_erro)
        
    if ping_result.get("error"):
        if ping_result.get("error") == "404_NOT_FOUND":
            logger.info("Entrou no 404_NOT_FOUND")
            _finaliza_task_com_erro(task, ping_result.get("message"))
        else:
            task.status = "Falha"
            task.traceback = ping_result.get("exception")
            task.end_time = timezone.now()
            task.save()
            # logger.error(f"Erro no ping: {ping_result.get("exception")}")
            raise Exception(f"Falha no ping: {ping_result.get('error')}")

    task.alive = ping_result.get("alive")
    task.inputHost = ping_result.get("inputHost") if getattr(ping_result, "produto", None) == "VM" else None
    task.avg_time = ping_result.get("avg")
    task.packet_loss = ping_result.get("packetLoss")
    task.ping_output = ping_result.get("output")
    task.status = "Concluido"
    task.resultado = "ping_ok" if ping_result.get("alive") else "ping_nok"


    if not ping_result.get("alive"):
        task.traceback = "Falha na conectividade"

    task.end_time = timezone.now()
    task.save()

from django.shortcuts import render
from datetime import datetime
from django.http import HttpRequest
from rest_framework.views import APIView
from celery.result import AsyncResult
from rest_framework.response import Response
from pingador.models import Task
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .conector_pingador.pingador_dados_facil import PingService
from drf_yasg.utils import swagger_auto_schema
import os
from drf_yasg import openapi
from rest_framework import status
from pingador.libs.health_check import Tools
from rest_framework.generics import RetrieveAPIView
import uuid
from .libs_conection.conections import busca_ip_cliente
from pingador.serializers import SolicitaTesteConectividadeSerializer
from pingador.serializers import ConsultarTesteConectividadeSerializer
from pingador.tasks import ProcessPingJornadaDigital
import logging



# Obtenha o logger configurado no settings.py
logger = logging.getLogger(__name__)

class SolicitaTesteConectividade(APIView):
    """
    API para solicitar testes de conectividade.
    """
    
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Solicitar Teste de Conectividade",
        operation_description=(
            "Este endpoint permite solicitar um teste de conectividade para produtos como VPN VIP, CN e VM. "
            "O teste é executado de forma assíncrona e retorna um `task_id` para acompanhamento."
        ),
        request_body=SolicitaTesteConectividadeSerializer,
        responses={
            201: openapi.Response(
                description="Tarefa criada com sucesso.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "task_id": openapi.Schema(type=openapi.TYPE_STRING, description="ID único da tarefa criada."),
                    },
                ),
            ),
            400: openapi.Response(
                description="Erro de validação nos dados enviados.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "field_name": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                    },
                    example={"circuito": ["Este campo é obrigatório."]},
                ),
            ),
            401: openapi.Response(
                description="Token informado é inválido.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, description="Mensagem de erro de autenticação."),
                    },
                    example={"detail": "As credenciais de autenticação não foram fornecidas."},
                ),
            ),
            500: openapi.Response(
                description="Erro interno do servidor.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "task_id": openapi.Schema(type=openapi.TYPE_STRING, description="Sempre será None em caso de erro interno."),
                        "errorKey": openapi.Schema(type=openapi.TYPE_STRING, description="Chave de erro."),
                        "details": openapi.Schema(type=openapi.TYPE_STRING, description="Mensagem detalhada sobre o erro."),
                    },
                    example={
                        "task_id": None,
                        "errorKey": "INTERNAL_SERVER_ERROR",
                        "details": "Erro ao processar a solicitação. Contacte o administrador do sistema.",
                    },
                ),
            ),
        },
    )
    def post(self, request):
        """
        Endpoint para criar uma tarefa de teste de conectividade.
        """
        serializer = SolicitaTesteConectividadeSerializer(data=request.data)

        # Log de requisição recebida
        if isinstance(request._request, HttpRequest):
            logger.info(
                f"Requisição Recebida: Método: {request.method}, Endpoint: {request.path}, Dados: {request.data}"
            )

        if not serializer.is_valid():
            logger.error(f"Erro de validação: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        circuito = serializer.validated_data.get('circuito')
        task_id = str(uuid.uuid4())

        buscar_dados = busca_ip_cliente(circuito)
        if not buscar_dados:
            return Response(
                {
                    "errorKey": "CIRCUIT_ERROR",
                    "details": 'O circuito deve ser um produto VPN VIP ou IP CONNECT',
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        try:
            
            logger.info(f"Gerando task_id:{task_id} para tarefa")
            # Chamada assíncrona do processamento
            
            current_time = timezone.now()
            request_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Horário de entrada da requisição: {request_time}")

            # Preparação dos dados da tarefa
            task_data = {
                'task_id': task_id,
                'circuito': circuito,
                'ipv4_cliente': None,
                'ip_backbone': None,
                'pe': None,
                'modelo_equipamento': None,
                'localizacao': None,
                'descricao': None,
                'start_time': None,
                'request_time': request_time,
                'end_time': None,
                'traceback': None,
            }

            # Criação do registro no banco de dados
            Task.objects.create(**task_data)
            logger.info(f"Tarefa criada com sucesso: {task_id}")

            task_result = ProcessPingJornadaDigital.apply_async(args=[circuito, task_id], kwargs={})
            
            return Response({'task_id': task_id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Captura de exceções gerais
            logger.exception(f"Erro ao criar tarefa para circuito {circuito}: {str(e)}")
            return Response(
                {
                    "task_id": None,
                    "errorKey": "INTERNAL_SERVER_ERROR",
                    "details": "Erro ao processar a solicitação. Contacte o administrador do sistema."                    
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConsultarTesteConectividade(RetrieveAPIView):
    """
    API para consultar os resultados de um teste de conectividade pelo task_id.
    """
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()
    serializer_class = ConsultarTesteConectividadeSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'task_id',
                openapi.IN_QUERY,
                description="ID da tarefa a ser consultada",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Sucesso - Dados da tarefa retornados com sucesso.",
                examples={
                    'application/json': [
                        {
                            "task_id": "37ed8048-4e97-4bc9-81c5-98459348a298",
                            "status": "Concluido",
                            "resultado": "ping_ok",
                            "circuito": "circuito_exemplo",
                            "ipv4_cliente": "192.168.1.1",
                            "packet_loss": "0%",
                            "details": "Ping executado com sucesso."
                        },
                        {
                            "task_id": "37ed8048-4e97-4bc9-81c5-98459348a298",
                            "status": "Concluido",
                            "resultado": "ping_nok",
                            "circuito": "circuito_exemplo",
                            "ipv4_cliente": "192.168.1.1",
                            "packet_loss": "100%",
                            "details": "Falha no ping."
                        }
                    ]
                }
            ),
            400: openapi.Response(
                description="Erro de Requisição - task_id ausente ou inválido.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "task_id": openapi.Schema(type=openapi.TYPE_STRING, description="ID da tarefa enviado (ou None)."),
                        "errorKey": openapi.Schema(type=openapi.TYPE_STRING, description="Chave do erro."),
                        "details": openapi.Schema(type=openapi.TYPE_STRING, description="Descrição detalhada do erro."),
                    },
                ),
            ),
            404: openapi.Response(
                description="Tarefa não encontrada.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "task_id": openapi.Schema(type=openapi.TYPE_STRING, description="ID da tarefa."),
                        "errorKey": openapi.Schema(type=openapi.TYPE_STRING, description="Chave do erro."),
                        "details": openapi.Schema(type=openapi.TYPE_STRING, description="Detalhes adicionais."),
                    },
                ),
            ),
            422: openapi.Response(
                description="Erro durante o processamento.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "task_id": openapi.Schema(type=openapi.TYPE_STRING, description="ID da tarefa."),
                        "errorKey": openapi.Schema(type=openapi.TYPE_STRING, description="Chave do erro."),
                        "details": openapi.Schema(type=openapi.TYPE_STRING, description="Traceback ou mensagem do erro."),
                    },
                ),
            ),
            500: openapi.Response(
                description="Erro interno no servidor.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "task_id": openapi.Schema(type=openapi.TYPE_STRING, description="ID da tarefa."),
                        "errorKey": openapi.Schema(type=openapi.TYPE_STRING, description="Chave do erro."),
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, description="Mensagem de erro."),
                    },
                ),
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        task_id = request.query_params.get('task_id') or request.data.get('task_id')

        if not task_id:
            return Response(
                {
                    "task_id": None,
                    "errorKey": "TASK_BAD_REQUEST",
                    "details": "O parâmetro 'task_id' é obrigatório para realizar a consulta."                    
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
             # Validar se task_id é um UUID válido
            uuid.UUID(task_id)
        except (ValueError, TypeError):
            # Tratar como tarefa não encontrada
            return Response(
                {
                    "task_id": task_id,
                    "errorKey": "TASK_NOT_FOUND",
                    "details": "A tarefa enviada não existe no banco de dados. Favor verificar task_id.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Buscar a tarefa diretamente no banco
        task = Task.objects.filter(task_id=task_id).first()

        if not task:
            return Response(
                {
                    "task_id": task_id,
                    "errorKey": "TASK_NOT_FOUND",
                    "details": "A tarefa enviada não existe no banco de dados. Favor validar task_id.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Mapear status do banco para resposta ao usuário
        if task.status == "Concluido":
            if task.resultado != "error":
                if task.resultado == "ping_ok":
                    serializer = self.get_serializer(task)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {
                        'task_id': task.task_id,
                        'circuito': task.circuito,
                        'ipv4_cliente': task.ipv4_cliente,
                        'resultado': task.resultado,
                        'packet_loss': task.packet_loss,
                        'status': task.status,
                        },
                        status=status.HTTP_200_OK,
                    )            
            else:
                return Response(
                    {
                        "task_id": task_id,
                        "errorKey": "PROCESSING_ERROR",
                        "details": task.traceback,
                    },
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

        elif task.status == "Pendente":
            return Response(
                {
                    "task_id": task_id,
                    "status": "PENDING",
                    "details": "A tarefa ainda não foi iniciada.",
                },
                status=status.HTTP_200_OK,
            )
        
        elif task.status == "Em andamento":
            return Response(
                {
                    "task_id": task_id,
                    "status": "IN_PROGRESS",
                    "details": "A tarefa está em andamento.",
                },
                status=status.HTTP_200_OK,
            )
        
        elif task.status == "Falha":
            return Response(
                {
                    "task_id": task_id,
                    "errorKey": "INTERNAL_SERVER_ERROR",
                    "detail": "Erro ao processar a tarefa. Contate o administrador do sistema.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Fallback para status desconhecidos
        return Response(
            {
                "task_id": task_id,
                "errorKey": "UNKNOWN",
                "detail": "O status da tarefa não é reconhecido. Contate o administrador do sistema.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    


class HealthCheckView(APIView):
    def __init__(self):
        self.instance = Tools()
    @swagger_auto_schema(

        responses={
            200: openapi.Response(
                description='Exemplo de resposta de sucesso',
                examples={
                    'application/json': {
                        "pingador_api": "up",
                        "database": "up",
                        "queues": "up",
                        "cpu_usage_percent": 0.2,
                        "memory_usage_percent": 28.1
                    }
                }
            ),
            500: 'Erro interno do servidor'
        },
        operation_summary="Health Check API Pingador", 
        operation_description='''Esta funcionalidade consiste em validar os serviços da api PINGADOR. Quando chamada com sucesso status 200(OK), ela retorna um dicionário indicando quais serviços está funcionando corretamente. Em caso de falha será retonado o status "down" para o item que está sendo validado. Em caso de erro interno, um código de status 500 (Internal Server Error) será retornado. Esta é uma operação simples usada para monitorar a disponibilidade do serviço.'''
    )
    def get(self, request):
        ENDPOINT = os.environ.get('ENDPOINT')
        ENDPOINT_VM = os.environ.get('ENDPOINT_VM')

        database_is_healthy = self.instance.check_database_health()
        check_resource_usage = self.instance.check_resource_usage()
        task_id = self.instance.get_valid_task_id()

        if task_id:
            check_async_tasks_health = self.instance.check_async_tasks_health(
                task_id)
        else:
            check_async_tasks_health = False

        ping_service = PingService()
        ping_result_vm = ping_service.ping(
            endpoint=ENDPOINT_VM,
            circuito="5010111",
            localidade="GOPA"
        )

        ping_result_cn = ping_service.ping(
            endpoint=ENDPOINT,
            numeric_host='187.12.31.86'
        )

        print(ping_result_vm.get("status_code"))
        print(ping_result_cn.get("status_code"))
        
        response_data = {
            'pingador_api': 'up' if ping_result_vm.get("status_code") == 200 and ping_result_cn.get("status_code") == 200 else 'down',
            'database': 'up' if database_is_healthy else 'down',
            'queues': 'up' if check_async_tasks_health else 'down',
            'cpu_usage_percent': check_resource_usage['cpu_usage_percent'] if check_resource_usage else 'down',
            'memory_usage_percent': check_resource_usage['memory_usage_percent'] if check_resource_usage else 'down',
        }

        return Response(response_data, status=200)
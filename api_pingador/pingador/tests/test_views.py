from rest_framework.test import APITestCase
from django.test.utils import override_settings
from rest_framework import status
from django.urls import reverse
import time
import logging

logger = logging.getLogger(__name__)

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TestSolicitaEConsultaPing(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url_solicita = reverse("SolicitaTesteConectividade")
        cls.url_consulta = reverse("ConsultarTesteConectividade")
        cls.circuitos = ["SDR5024995", "SDR5025000", "SDR5024997"]

    def test_fluxo_completo_ping(self):
        for circuito in self.circuitos:
            # Passo 1: Solicitar o ping
            payload = {"circuito": circuito}
            response = self.client.post(self.url_solicita, payload, format="json")
            self.assertEqual(response.status_code, 201)

            task_id = response.data["task_id"]
            logger.info(f"Tarefa criada para o circuito {circuito}, task_id: {task_id}")

            # Passo 2: Consultar o status da tarefa
            start_time = time.time()
            timeout = 30  # Tempo máximo de espera em segundos
            status = None
            resultado = None

            while time.time() - start_time < timeout:
                consulta_response = self.client.get(self.url_consulta, {'task_id': task_id})
                self.assertIn(consulta_response.status_code, [200, 202])  # 202 = Processando, 200 = Concluído

                status = consulta_response.data.get("status")
                if status == "Concluído":
                    resultado = consulta_response.data.get("resultado")
                    break
                elif status == "Falha":
                    logger.error(f"Tarefa {task_id} falhou: {consulta_response.data.get('traceback')}")
                    self.fail(f"Tarefa {task_id} falhou.")
                time.sleep(1)  # Aguardar 1 segundo antes de nova tentativa

            # Verificar se o tempo esgotou
            if status != "Concluído":
                self.fail(f"Tarefa {task_id} não foi concluída dentro do tempo limite.")

            # Passo 3: Logar os resultados
            elapsed_time = round(time.time() - start_time, 2)
            logger.info(f"Ping realizado para circuito {circuito}: Resultado: {resultado}, Tempo total: {elapsed_time}s")

            # Verifica o resultado retornado pela API
            self.assertIn(resultado, ["ping_ok", "ping_nok"])



import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Dict, Any, Union, Optional
import os
from dotenv import load_dotenv
import logging
import urllib3

logger = logging.getLogger(__name__)

load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PingService:
    """
    Classe para gerenciar chamadas de ping na API de homologação.
    Suporte para timeout, retry e escalabilidade.
    """
    TOKEN = os.environ.get('TOKEN')
    BASE_URL = os.environ.get('BASE_URL')
    HEADERS = {"Content-Type": "application/json",
               "Authorization": f"Bearer {TOKEN}"}

    def __init__(self, timeout: int = 10, retries: int = 3, backoff_factor: float = 0.3):
        """
        Inicializa o serviço com configurações de timeout e retry.
        :param timeout: Tempo máximo para resposta em segundos.
        :param retries: Número de tentativas em caso de falha.
        :param backoff_factor: Intervalo exponencial entre tentativas.
        """
        if not self.TOKEN or not self.BASE_URL:
            raise ValueError("TOKEN, BASE_URL não configurados corretamente no arquivo .env")

        self.timeout = timeout
        self.session = requests.Session()

        # Configuração de retries
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],  # Incluindo POST
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

    def ping(self, numeric_host: Optional[str] = None, endpoint: str = None, circuito: Optional[str] = None, localidade: Optional[str] = None) -> Union[Dict[str, Any], str]: # type: ignore
        """
        Realiza o teste de ping através da API.
        :param numeric_host: Endereço IP de destino.
        :return: Resposta JSON em caso de sucesso, ou string de erro.
        """
        url = f"{self.BASE_URL}{endpoint}"

        # Define o payload com base nos parâmetros fornecidos de produto VM ou CN
        if endpoint and "VM" in endpoint.upper():
            if not circuito or not localidade:
                raise ValueError("Para o endpoint VM, 'circuito' e 'localidade' são obrigatórios.")
            payload = {"circuito": circuito, "localidade": localidade}
        else:
            if not numeric_host:
                raise ValueError("para endpoints CN, 'numeric_host' é obrigatório.")
            payload = {"numeric_host": numeric_host}
        
        # logger.info(f"Enviando payload para {url}: {payload}")

        try:
            response = self.session.post(
                url, json=payload, headers=self.HEADERS, verify=False, timeout=self.timeout
            )

            # Tratamento específico para o erro 404
            if response.status_code == 404:
                return {"error": "404_NOT_FOUND", "message": "Recurso não encontrado para circuito"}
            
            response.raise_for_status()

            try:
                data = response.json()
                logger.info(f"Teste de ping realizado.")
                return {"status_code": response.status_code, "data": data}
            
            except ValueError:
                return {
                    "status_code": response.status_code,
                    "error": "INVALID_JSON",
                    "message": "Resposta inválida do servidor"
                }
            
        except requests.exceptions.RequestException as e:
            # Log de erro para depuração
            return {
                "status_code": None,
                "error": "COMUNICACAO_FALHOU",
                "message": f"Falha na comunicação com a API: {str(e)}"
            }


# Teste local da classe
# if __name__ == "__main__":
#     ping_service = PingService()
#     ip_test = "8.8.8.8"  # Google DNS
#     result = ping_service.ping(ip_test)
#     print(result)

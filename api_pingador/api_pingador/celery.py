from __future__ import absolute_import, unicode_literals
import os
from pathlib import Path
from dotenv import load_dotenv
from celery import Celery
from django.conf import settings

# Carrega variáveis de ambiente
load_dotenv()

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuração do Django como backend
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_pingador.settings')

# Configurações de credenciais
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')

# Inicialização do Celery
app = Celery('api_pingador')

# Configuração padrão do Celery para o Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configuração de Broker e Backend
app.conf.BROKER_URL = f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@rabbitmq:5672/api_pingador_celery'
app.conf.RESULT_BACKEND = f'db+postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5432/{POSTGRES_DB}'

# Descoberta automática de tasks
app.autodiscover_tasks()

# Roteamento de tasks para filas específicas
app.conf.task_routes = {
    'api_pingador.pingador.tasks.ProcessPingJornadaDigital': {'queue': 'jornada_digital_queue'},
}

app.conf.task_track_started = True

# Configurações de desempenho do worker
app.conf.worker_concurrency = 8  # Threads simultâneas
app.conf.task_acks_late = True  # Habilitar confirmação tardia

# Configurações de serialização
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# Tarefa de debug
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

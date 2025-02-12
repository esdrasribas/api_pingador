from django.db import connection
from ..models import Task
import psutil


class Tools:
    # HC Banco de dados
    def check_database_health(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    return True
        except Exception as e:
            print(f"Database check failed: {e}")
        return False

    # HC recursos utilizados
    def check_resource_usage(self):
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent

        if cpu_usage > 90 or memory_usage > 90:
            return False
        return {
            "cpu_usage_percent": cpu_usage,
            "memory_usage_percent": memory_usage,
        }


    # HC das tarefas celery
    def check_async_tasks_health(self, task_id):
        try:
            task = Task.objects.get(task_id=task_id)

            if task.status == 'Concluido':
                return True
            else:
                return False
        except Exception as e:
            print(f"Async task check failed: {e}")
            return False
        

    # Consulta o banco de dados para obter o primeiro task_id com status 'ATIVO'
    def get_valid_task_id(self):
        try:

            task = Task.objects.filter(status='Concluido').order_by('id').first()
            print(task.task_id)

            if task:
                return task.task_id
            else:
                return None
        except Exception as e:
            print(f"Error fetching a valid task_id: {e}")
            return None
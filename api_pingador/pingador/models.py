from django.db import models
import uuid

# Create your models here.

class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_id = models.UUIDField(unique=True, help_text="ID da tarefa", editable=False)
    circuito = models.CharField(max_length=20, help_text="Circuito", default='')
    ipv4_cliente = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True, help_text="Endereço IPv4 do cliente")
    ip_backbone = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True, help_text="Ip do backbone")
    inputHost = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True, help_text="Endereço NAT do clietne")
    pe = models.CharField(max_length=50, null=True, blank=True, help_text="PE do circuito")
    modelo_equipamento = models.CharField(max_length=50, null=True, blank=True, help_text="Modelo do equipamento")
    localizacao = models.CharField(max_length=50, null=True, blank=True, help_text="localizacao do cliente")
    produto = models.CharField(max_length=50, null=True, blank=True, help_text="produto do cliente")
    ccto = models.CharField(max_length=50, null=True, blank=True, help_text="Identificador número do circuito")
    start_time = models.DateTimeField(auto_now_add=True, help_text="Data e hora de início")
    end_time = models.DateTimeField(null=True, blank=True, help_text="Data e hora de conclusão")
    traceback = models.TextField(null=True, blank=True, help_text="Rastreamento da exceção")
    request_time = models.DateTimeField(auto_now=True, help_text="Data e hora da solicitação")
    retorno_pingador = models.CharField(max_length=255, null=True, blank=True, help_text="Output chamada pingador")
    descricao = models.TextField(null=True, blank=True, help_text="Rastreamento da exceção")
    status = models.CharField(max_length=255, default="Pendente")
    resultado = models.CharField(max_length=20, help_text="Resultado final", default='')
    packet_loss = models.CharField(max_length=255, null=True, blank=True)
    ping_output = models.TextField(null=True, blank=True)
    alive = models.BooleanField(null=True, blank=True)
    avg_time = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.task_id}'
    


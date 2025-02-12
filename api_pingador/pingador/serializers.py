from rest_framework import serializers
from django.core.validators import RegexValidator
from pingador.models import Task

class SolicitaTesteConectividadeSerializer(serializers.Serializer):
    circuito = serializers.CharField(
            validators=[
                RegexValidator(
                regex= r'^[A-Z]{3,4}\d{7,10}$',
                message='O campo circuito está fora do pádrão. Favor enviar conforme exemplo: RJO987654.'
            )
        ]
    )

class ConsultarTesteConectividadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'task_id',
            'circuito',
            'ipv4_cliente',
            'resultado',
            'packet_loss',
            'avg_time',
            'status',
        ]
from django.contrib import admin
from .models import Task

class TaskAdmin(admin.ModelAdmin):
    readonly_fields = ('start_time',)
    fields = ('circuito', 'ipv4_cliente', 'ip_backbone', 'inputHost', 'pe','ccto', 'modelo_equipamento', 'localizacao', 'produto', 'start_time', 'end_time', 'resultado', 'traceback', 'retorno_pingador', 'descricao', 'status', 'packet_loss', 'ping_output','alive', 'avg_time')
    list_display = ('task_id',  'start_time', 'circuito', 'ipv4_cliente','produto', 'resultado', 'status')


admin.site.register(Task, TaskAdmin)
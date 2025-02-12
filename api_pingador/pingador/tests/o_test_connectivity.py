from ping3 import ping

# Alvos para teste de conectividade
targets = {
    "rabbitmq": "rabbitmq",
    "celery": "celery",
    "pingador_db": "pingador_db"
}

print("Iniciando testes de conectividade...\n")

for name, ip in targets.items():
    try:
        response = ping(ip)
        if response:
            print(f"Conectado a {name} ({ip}) com latência de {response:.2f} ms.")
        else:
            print(f"Falha ao conectar a {name} ({ip}).")
    except Exception as e:
        print(f"Erro ao testar conexão com {name} ({ip}): {e}")

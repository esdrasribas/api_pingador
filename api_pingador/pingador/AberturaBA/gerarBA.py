import requests

# URL base da API
BASE_URL = "http://10.121.189.131:8012/inserirAlerta/"

# Testar conexão com a API
def testar_conexao():
    response = requests.get(f"{BASE_URL}testarConexao/")
    return response.json()

# Obter o último registro inserido
def obter_ultimo_registro():
    response = requests.get(f"{BASE_URL}ultimoRegistro/")
    return response.json()

# Inserir um alerta na API
def inserir_alerta():
    payload = {
        "Summary": "INDISPONIBILIDADE API PINGADOR",
        "AdditionalText": "HEALTH CHECK API PINGADOR",
        "AlertKey": "P230PLA",
        "Node": "PLIF",
        "NodeAlias": "TESTGER",
        "Agent": "0",
        "AlertGroup": "HC_GVA",
        "Severity": "0",
        "EventTime": "2025-02-04 12:00:00",
        "EventType": "GER",
        "SpecificProblem": "Problema detectado no pingador",
        "AdditionalInformation": "Teste de geração de alerta",
        "Uf": "SP",
        "Localidade": "São Paulo",
        "Estacao": "N/A",
        "Agrupamento": "PLT",
        "Matricula": "CNGI0",
        "Type": "SEMTIPO",
        "FonteInformante": "HCA",
        "TechArea": "PLIF",
        "Mnemonio": "P230PLA",
        "Domain": "HC_GVA",
        "Technology": "NC",
        "Url": "http://link-do-incidente",
        "InsertDate": "2025-02-04 12:00:00",
        "ProbableCause": "Erro de comunicação",
        "ComplAgrup": "PLT",
        "DocAssociado": None,
        "PhysicalSlot": None,
        "PhysicalPort": None,
        "PhysicalCard": None,
        "PhysicalShelf": None,
        "FlagSGE": "S",
        "Cos": "0",
        "InputControl": "N",
        "Criticality": "N",
        "ExpireTime": "1800"
    }

    response = requests.post(f"{BASE_URL}inserirAlerta/", json=payload)
    return response.json()

if __name__ == "__main__":
    # Testa conexão
    conexao = testar_conexao()
    print("Teste de Conexão:", conexao)

    # Insere um alerta
    resultado = inserir_alerta()
    print("Resultado da Inserção:", resultado)

    # Obtém o último registro inserido
    ultimo_registro = obter_ultimo_registro()
    print("Último Registro:", ultimo_registro)

import requests
from concurrent.futures import ThreadPoolExecutor
import json

# URL da API
API_URL = "https://suaapi.com/api/v1/SolicitaTesteConectividade/"

# Configuração de cabeçalhos, se necessário
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer seu_token_aqui"
}

# Lista de circuitos a serem testados
circuitos = [
    "SDR5024995",
    "SDR5025000",
    "SDR5025001",
    "SDR5025002"
]

# Máximo de requisições simultâneas
CONCURRENT_REQUESTS = 10  # Ajustável conforme necessário

def make_request(circuito):
    """Faz uma chamada POST para a API com um circuito."""
    payload = {"circuito": circuito}
    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        return {
            "status_code": response.status_code,
            "task_id": response.json().get("task_id", "N/A"),
            "error": None if response.status_code == 201 else response.text,
        }
    except Exception as e:
        return {
            "status_code": None,
            "task_id": None,
            "error": str(e),
        }

def main():
    """Executa as requisições simultâneas."""
    results = []
    total_tests = len(circuitos)
    print(f"Iniciando testes com {total_tests} circuitos e até {CONCURRENT_REQUESTS} requisições simultâneas.\n")

    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = {executor.submit(make_request, circuito): circuito for circuito in circuitos}

        for future in futures:
            result = future.result()
            results.append(result)
            circuito = futures[future]
            print(f"Circuito: {circuito} | Status Code: {result['status_code']} | Task ID: {result['task_id']} | Error: {result['error']}")

    # Salvar resultados em um arquivo JSON
    with open("test_results.json", "w") as file:
        json.dump(results, file, indent=4)

    print(f"\nTeste concluído! Resultados salvos em 'test_results.json'. Total de circuitos testados: {total_tests}.")

if __name__ == "__main__":
    main()

import requests

url = 'http://127.0.0.1:5000/upload_excel'  # URL do endpoint da API

file_path = 'Lote.xlsx'  # Substitua pelo caminho do seu arquivo Excel

# Abre o arquivo em modo binário
with open(file_path, 'rb') as file:
    files = {'file': file}
    response = requests.post(url, files=files)

# Exibe a resposta da API
print(response.status_code)
print(response.json())

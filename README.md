# Artabas API

API desenvolvida em Flask para raspagem de dados de preços de ovos e outros produtos agrícolas, além de processamento de arquivos Excel e armazenamento de dados no MongoDB.

## Funcionalidades

1. **Raspagem de Dados (Scraping)**:
   - Raspagem de dados do site Ovos Online para obter informações como:
     - Preços do Dólar.
     - Preços de Milho, Farelo de Soja e Ovos Tipo Extra.
   - Endpoint: `/api/eggs_online` (GET)
   
   - Também há suporte para:
     - Preços de ovos para datas específicas.
     - Endpoint: `/api/egg-prices` (GET)

2. **Upload e Processamento de Arquivos Excel**:
   - Upload de arquivos Excel, processamento de dados e armazenamento no MongoDB.
   - Endpoint: `/upload_excel` (POST)

3. **Consulta de Dados no MongoDB**:
   - Retorna dados agregados relacionados a estatísticas diárias de aves e ração, armazenados no MongoDB.
   - Endpoint: `/getData` (GET)

## Como Executar o Projeto

### Requisitos

- Python 3.7 ou superior
- MongoDB
- Instalar as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```
Variáveis de Ambiente
As seguintes variáveis de ambiente precisam ser configuradas:

MONGODB_URI: URI de conexão para o MongoDB.
Executando o Servidor
Clone este repositório:
```bash
Copy code
git clone https://github.com/seu-usuario/artabas-api.git
cd artabas-api
```
Inicie o servidor Flask:
```bash
Copy code
python app.py
O servidor será iniciado no endereço http://127.0.0.1:5000.
```

Endpoints
1. Raspagem de Dados do Ovos Online
URL: /api/eggs_online
Método: GET
Descrição: Retorna os dados de preços do site Ovos Online.

2. Preços de Ovos por Data
URL: /api/egg-prices?date=YYYY-MM-DD
Método: GET
Descrição: Retorna os preços de ovos para uma data específica.

3. Upload de Arquivo Excel
URL: /upload_excel
Método: POST
Descrição: Permite o upload de um arquivo Excel para processamento e armazenamento no MongoDB.

4. Consulta de Dados do MongoDB
URL: /getData
Método: GET
Descrição: Retorna dados agregados do MongoDB, como total de aves mortas e ração consumida por dia.

Estrutura do Projeto
```bash
Copy code
.
├── app.py               # Código principal da aplicação Flask
├── upload.py            # Módulo para processamento de arquivos Excel
├── requirements.txt     # Dependências do projeto
└── README.md            # Este arquivo
```

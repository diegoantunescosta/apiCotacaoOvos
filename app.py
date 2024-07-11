from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from flasgger import Swagger
from flask_cors import CORS
import threading
from datetime import datetime
from flask import Flask, request, jsonify
import os
from flasgger import Swagger
from upload import process_excel, save_to_mongodb
from bson.json_util import dumps
from pymongo import MongoClient


app = Flask(__name__)
CORS(app)

swagger = Swagger(app)

URI = os.getenv('MONGODB_URI')
client = MongoClient(URI)
db = client['Artabas']
collection = db['Aplicativo']

def scraping_ovos_online():
    url = 'https://www.ovoonline.com.br/'
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        dolar_info = []
        dolar_td = soup.find('td', string=lambda text: text and 'Valores do d' in text)
        if dolar_td:
            dolar_text = dolar_td.text.strip()
            dolar_values = dolar_text.split(':')
            data_atual = dolar_values[0].split('em')[1].split(',')[0].strip()
            valores = [
                dolar_values[1].split(',')[0].strip() + ',' + dolar_values[1].split(',')[1].strip().split(' ')[0],
                dolar_values[2].split(',')[0].strip() + ',' + dolar_values[2].split(',')[1].strip().split(' ')[0],
                dolar_values[3].split(',')[0].strip() + ',' + dolar_values[3].split(',')[1].strip().split(' ')[0]
            ]
            periodos = [data_atual, "30 dias", "1 ano"]
            for i, valor in enumerate(valores):
                if i < len(periodos):
                    dolar_info.append({
                        "Periodo": periodos[i],
                        "Dolar": "R$" + valor
                    })
        
        milho_valores = []
        farelo_valores = []
        ovos_valores = []
        
        tables = soup.find_all('table', width='460')
        
        for table in tables:
            titulo = table.find_previous('td', bgcolor='#F9C239')
            if titulo and 'Milho' in titulo.text:
                milho_rows = table.find_all('td', align='center')
                milho_valores.extend([clean_value(row.text.strip()) for row in milho_rows])
            elif titulo and 'Farelo de soja' in titulo.text:
                farelo_rows = table.find_all('td', align='center')
                farelo_valores.extend([clean_value(row.text.strip()) for row in farelo_rows])
            elif titulo and 'Ovos tipo Extra' in titulo.text:
                ovos_rows = table.find_all('td', align='center')
                ovos_valores.extend([clean_value(row.text.strip()) for row in ovos_rows])
        
        dados = {
            "Valores do Dolar": dolar_info,
            "Milho": organize_values(milho_valores, periodos),
            "Farelo de Soja": organize_values(farelo_valores, periodos),
            "Ovos Tipo Extra": organize_values(ovos_valores, periodos),
        }
        
        return dados
    else:
        return {"error": f'Falha ao acessar o site. Código de status: {response.status_code}'}

def clean_value(value):
    value = value.replace('R$', '').replace('$', '').replace('\n', '').replace('*', '').replace(',', '.').strip()
    return value

def organize_values(values, periodos):
    organized = []
    for i in range(0, len(values), 2):
        price = values[i]
        exchange = values[i + 1] if i + 1 < len(values) else ''
        periodo = periodos[i//2] if i//2 < len(periodos) else ''
        organized.append({
            "Periodo": periodo,
            "preco": price,
            "Cambio": exchange
        })
    return organized

@app.route('/api/eggs_online', methods=['GET'])
def get_ovos_online():
    """
    Endpoint para obter dados do site Ovos Online
    ---
    responses:
      200:
        description: Dados extraídos com sucesso
        schema:
          type: object
          properties:
            Valores do Dolar:
              type: array
              items:
                type: object
                properties:
                  Periodo:
                    type: string
                  Dolar:
                    type: string
            Milho:
              type: array
              items:
                type: object
                properties:
                  Periodo:
                    type: string
                  preco:
                    type: string
                  Cambio:
                    type: string
            Farelo de Soja:
              type: array
              items:
                type: object
                properties:
                  Periodo:
                    type: string
                  preco:
                    type: string
                  Cambio:
                    type: string
            Ovos Tipo Extra:
              type: array
              items:
                type: object
                properties:
                  Periodo:
                    type: string
                  preco:
                    type: string
                  Cambio:
                    type: string
    """
    dados_scraped = scraping_ovos_online()
    return jsonify(dados_scraped)

def scrape_ovo_online_statistics():
    """
    Scrape statistics data from the Ovo Online website.

    Returns:
    dict: Dictionary containing scraped data.
    """
    url = 'https://www.ovoonline.com.br/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    main_table = soup.find('table', width='460')

    if not main_table:
        return None

    rows = main_table.find_all('tr')

    data = {}
    current_category = None

    for row in rows:
        cells = row.find_all('td')

        if len(cells) == 1 and 'ESTAT&Iacute;STICA' in cells[0].text:
            current_category = cells[0].text.strip()

        elif len(cells) >= 10:
            if current_category:
                category_data = {
                    "Preço Atual": cells[0].text.strip(),
                    "Variação 30 dias": cells[2].text.strip(),
                    "Preço 30 dias": cells[4].text.strip(),
                    "Variação 1 ano": cells[6].text.strip(),
                    "Preço 1 ano": cells[8].text.strip()
                }
                data[current_category] = category_data

    return data

def scrape_egg_prices(date):
    """
    Scrape egg prices data from a website for a given date.

    Parameters:
    date (str): The date in format YYYY-MM-DD.

    Returns:
    list: List of dictionaries containing scraped data.
    """
    formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
    url = f'https://www.noticiasagricolas.com.br/cotacoes/ovos/precos-de-ovos-cepea-produto-a-retirar-bastos/{formatted_date}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table', class_='cot-fisicas')
    if not table:
        return None  

    rows = table.find_all('tr')[1:]  

    data = []
    for row in rows:
        cols = row.find_all('td')
        if cols[0].text.strip():  
            item = {
                "Data": cols[0].text.strip(),
                "Regiao/Tipo": cols[1].text.strip(),
                "Preco (R$/30 dz)": float(cols[2].text.strip().replace(',', '.')),
                "Variacao/Semana (%)": float(cols[3].text.strip().replace(',', '.').replace('+', '').replace('%', ''))
            }
            data.append(item)
    
    return data


@app.route('/api/egg-prices', methods=['GET'])
def get_egg_prices():
    """
    Retrieve egg prices data for a given date.
    
    ---
    parameters:
      - name: date
        in: query
        type: string
        required: true
        description: The date in format YYYY-MM-DD.
    
    responses:
      200:
        description: A list of egg prices data.
        schema:
          type: array
          items:
            type: object
            properties:
              Data:
                type: string
                description: Date of the price data.
              Região/Tipo:
                type: string
                description: Region or type of eggs.
              Preço (R$/30 dz):
                type: number
                description: Price per 30 dozen eggs in R$.
              Variação/Semana (%):
                type: number
                description: Week variation percentage.
      400:
        description: Bad request, invalid date format or missing date.
      404:
        description: No records found for the provided date.
    """
    date = request.args.get('date')
    if not date:
        return jsonify({"error": "Please provide a date in the format YYYY-MM-DD"}), 400
    try:
        data = scrape_egg_prices(date)
        if data is None:
            return jsonify({"error": "No records found for this date."}), 404
        else:
            return jsonify(data)
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400
    

@app.route('/upload_excel', methods=['POST'])
def upload_file():
    """
    Upload an Excel file and process its data.
    ---
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: The Excel file to upload
    responses:
      200:
        description: File processed and data saved to MongoDB
      400:
        description: No file part or no selected file
      500:
        description: Failed to process the Excel file or save data to MongoDB
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        file_path = os.path.join('/tmp', file.filename)
        file.save(file_path)
        data = process_excel(file_path)
        if data:
            if save_to_mongodb(data):
                return jsonify({"success": "File processed and data saved to MongoDB"}), 200
            else:
                return jsonify({"error": "Failed to save data to MongoDB"}), 500
        else:
            return jsonify({"error": "Failed to process the Excel file"}), 500
        


@app.route('/getData', methods=['GET'])
def get_data():
    """
    Retorna dados do MongoDB relacionados às planilhas.
    ---
    
    description: Retorna estatísticas agregadas das planilhas do MongoDB.
    responses:
      200:
        description: Dados extraídos com sucesso
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  Sheet:
                    type: string
                    description: Nome da planilha
                  TotalAvesMortas:
                    type: integer
                    description: Total de aves mortas na planilha
                  TotalPrevistoRacao:
                    type: integer
                    description: Total previsto de ração na planilha
                  TotalRealRacao:
                    type: integer
                    description: Total real de ração na planilha
      500:
        description: Erro interno no servidor
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Mensagem de erro detalhada
    """
  
    try:
        sheets = collection.distinct('Sheet')
        all_data = []

        for sheet in sheets:
            data = list(collection.find({'Sheet': sheet}))
            total_aves_mortas = 0
            total_previsto_racao = 0
            total_real_racao = 0

            for entry in data:
                for tabela in entry['Data']['Tabela']:
                    if isinstance(tabela['Aves Mortas'], int):
                        total_aves_mortas += tabela['Aves Mortas']

                    previsto_racao = tabela.get('Previsto Ração', 0)
                    if isinstance(previsto_racao, (int, float)):
                        total_previsto_racao += previsto_racao

                    real_racao = tabela.get('Real Ração', 0)
                    if isinstance(real_racao, (int, float)):
                        total_real_racao += real_racao

            total_previsto_racao = round(total_previsto_racao)

            sheet_data = {
                'Sheet': sheet,
                'TotalAvesMortas': total_aves_mortas,
                'TotalPrevistoRacao': total_previsto_racao,
                'TotalRealRacao': total_real_racao,
            }

            all_data.append(sheet_data)

        return jsonify(all_data), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def call_api_every_minute():
    try:
        response = requests.get('https://apicotacaoovos.onrender.com/api/eggs_online')
        print(f"Status code: {response.status_code}, Response: {response.json()}")
    except Exception as e:
        print(f"Failed to call API: {e}")
    threading.Timer(60, call_api_every_minute).start()


if __name__ == '__main__':
    threading.Timer(1, call_api_every_minute).start()
    app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from flasgger import Swagger
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


swagger = Swagger(app)

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

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000 ,debug=True)

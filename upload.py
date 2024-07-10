import openpyxl
import json
from datetime import datetime
from flask import Flask, request, jsonify
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

URI = os.getenv("MONGODB_URI", "mongodb+srv://default:default@cluster0.ifc5n.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

def save_object_to_json(data, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print(f'Objeto salvo com sucesso em {file_path}')
    except Exception as e:
        print(f'Erro ao salvar o objeto como JSON: {e}')

def process_excel(file_path):
    try:
        workbook = openpyxl.load_workbook(file_path, data_only=True)  # Carrega o arquivo Excel com valores calculados
        sheet = workbook.active  # Obtém a primeira planilha ativa

        # Monta os dados para enviar para a API
        data = {
            "Granja": sheet['B1'].value if sheet['B1'].value else '',
            "Genética": sheet['B2'].value if sheet['B2'].value else '',
            "Data Nasc.": sheet['B3'].value.strftime('%Y-%m-%d') if isinstance(sheet['B3'].value, datetime) else '',
            "Lote": sheet['B4'].value if sheet['B4'].value else '',
            "Quant. Inicial Aves": sheet['G1'].value if sheet['G1'].value else '',
            "Galpão Cria": sheet['G2'].value if sheet['G2'].value else '',
            "Galpão Recria": sheet['G3'].value if sheet['G3'].value else '',
            "Galpão Postura": sheet['G4'].value if sheet['G4'].value else '',
            "Cria/Recria": sheet['M1'].value if sheet['M1'].value else '',
            "Postura": sheet['M2'].value if sheet['M2'].value else '',
            "N1": sheet['N1'].value if sheet['N1'].value else '',
            "N2": sheet['N2'].value if sheet['N2'].value else ''
        }

        tabela_dados = []
        for row in sheet.iter_rows(min_row=7, values_only=True):
            if any(row):  # Verifica se a linha não está vazia
                tabela_dados.append({
                    "Data": row[0].strftime('%Y-%m-%d') if isinstance(row[0], datetime) else '',
                    "Semana": row[1] if row[1] else '',
                    "Dia": row[2] if row[2] else '',
                    "Aves Mortas": row[3] if row[3] else '',
                    "Previsto %": row[4] if row[4] else '',
                    "Previsto Aves": row[5] if row[5] else '',
                    "Real Aves": row[6] if row[6] else '',
                    "Previsto % Ovos": row[7] if row[7] else '',
                    "Previsto Qtde Ovos": row[8] if row[8] else '',
                    "Real Ovos": row[9] if row[9] else '',
                    "Real % Ovos": row[10] if row[10] else '',
                    "Previsto Ração": row[11] if row[11] else '',
                    "Real Ração": row[12] if row[12] else ''
                })

        # Adiciona a lista de dados à estrutura JSON
        data["Tabela"] = tabela_dados

        return data

    except Exception as e:
        print(f'Erro ao processar o arquivo Excel: {e}')
        return None

def save_to_mongodb(data):
    try:
        client = MongoClient(URI, server_api=ServerApi('1'))

        try:
            client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)
            return False

        db = client['Artabas']  # Substitua pelo nome do seu banco de dados
        collection = db['Aplicativo']  # Substitua pelo nome da sua coleção

        collection.insert_one(data)
        print('Dados inseridos com sucesso no MongoDB')
        return True

    except Exception as e:
        print(f'Erro ao salvar os dados no MongoDB: {e}')
        return False



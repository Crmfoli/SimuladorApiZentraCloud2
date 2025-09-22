# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 7.0 - DASHBOARD DINÂMICO)
#
#   - Adiciona uma rota de API (/api/dados_atuais) que retorna dados em JSON.
#   - A página HTML usará JavaScript para chamar essa API e se atualizar.
# ===================================================================================

import random
from datetime import datetime, timedelta
# jsonify transforma dicionários Python em respostas JSON para APIs
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def gerar_dados_iniciais(device_id):
    """Gera a primeira carga de dados para a tabela."""
    dados_gerados = []
    hora_atual = datetime.now()
    for i in range(10):
        timestamp = hora_atual - timedelta(minutes=(9-i)*2) # Gera dados passados
        leitura = {
            "Horario": timestamp.strftime('%d/%m/%Y %H:%M:%S'),
            "Umidade": round(random.uniform(34.0, 36.0), 2),
            "Temperatura": round(random.uniform(20.0, 22.0), 2),
            "Chuva": round(random.uniform(0.0, 0.2), 2) if random.random() > 0.9 else 0.0
        }
        dados_gerados.append(leitura)
    return dados_gerados

def gerar_nova_leitura():
    """Gera apenas UMA nova leitura de dados."""
    timestamp = datetime.now()
    leitura = {
        "Horario": timestamp.strftime('%d/%m/%Y %H:%M:%S'),
        "Umidade": round(random.uniform(34.0, 36.0), 2),
        "Temperatura": round(random.uniform(20.0, 22.0), 2),
        "Chuva": round(random.uniform(0.0, 1.5), 2) if random.random() > 0.95 else 0.0
    }
    return leitura

# --- ROTAS DA NOSSA APLICAÇÃO ---

@app.route('/')
def pagina_de_acesso():
    """Mostra a página do formulário de login."""
    return render_template('index.html')

@app.route('/dados', methods=['POST'])
def mostrar_dados():
    """Renderiza a página inicial do dashboard com os primeiros 10 dados."""
    device_id = request.form['device_id']
    dados_iniciais = gerar_dados_iniciais(device_id)
    return render_template('dados.html', leituras=dados_iniciais, device_id=device_id)

# --- NOSSA NOVA ROTA DE API ---
@app.route('/api/dados_atuais')
def api_dados_atuais():
    """
    Esta é a nossa API. Ela não retorna HTML.
    Ela retorna os dados de uma nova leitura em formato JSON.
    O JavaScript irá chamar esta URL a cada 2 segundos.
    """
    nova_leitura = gerar_nova_leitura()
    return jsonify(nova_leitura)

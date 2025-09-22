# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 11.0 - CORREÇÃO DE FUSO HORÁRIO)
#
#   - Garante que todos os timestamps gerados estejam no horário de Brasília (America/Sao_Paulo).
# ===================================================================================

import random
# NOVO: Adicionamos a importação da classe ZoneInfo
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# NOVO: Definimos o fuso horário de Brasília como uma constante
TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")

# --- FUNÇÕES DE GERAÇÃO DE DADOS ---

def gerar_dados_historicos(pontos=30):
    """Gera uma lista de dados históricos para popular o dashboard inicial."""
    dados = []
    # ALTERADO: Usamos o fuso horário de Brasília aqui
    hora_atual = datetime.now(TZ_BRASILIA)
    for i in range(pontos):
        timestamp = hora_atual - timedelta(minutes=(pontos - 1 - i) * 2)
        leitura = {
            "timestamp_completo": timestamp.strftime('%d/%m/%Y %H:%M:%S'),
            "timestamp_grafico": timestamp.strftime('%H:%M:%S'),
            "umidade": round(random.uniform(30.0, 40.0), 2),
            "temperatura": round(random.uniform(20.0, 28.0), 2),
            "chuva": round(random.uniform(0.0, 2.0), 2) if random.random() > 0.85 else 0.0
        }
        dados.append(leitura)
    return dados

def gerar_nova_leitura():
    """Gera apenas UMA nova leitura de dados para a atualização em tempo real."""
    # ALTERADO: E usamos o fuso horário de Brasília aqui também
    timestamp = datetime.now(TZ_BRASILIA)
    return {
        "timestamp_completo": timestamp.strftime('%d/%m/%Y %H:%M:%S'),
        "timestamp_grafico": timestamp.strftime('%H:%M:%S'),
        "umidade": round(random.uniform(30.0, 40.0), 2),
        "temperatura": round(random.uniform(20.0, 28.0), 2),
        "chuva": round(random.uniform(0.0, 2.0), 2) if random.random() > 0.95 else 0.0
    }

# --- ROTAS DA APLICAÇÃO (sem alterações) ---

@app.route('/')
def pagina_de_acesso():
    return render_template('index.html')

@app.route('/dados', methods=['POST'])
def mostrar_dados():
    device_id = request.form['device_id']
    return render_template('dados.html', device_id=device_id)

@app.route('/grafico/<tipo_sensor>')
def pagina_grafico_individual(tipo_sensor):
    info_sensores = {
        'umidade': {'titulo': 'Umidade do Solo (%)', 'cor': 'rgba(54, 162, 235, 1)'},
        'temperatura': {'titulo': 'Temperatura do Solo (°C)', 'cor': 'rgba(255, 99, 132, 1)'},
        'chuva': {'titulo': 'Precipitação (mm)', 'cor': 'rgba(75, 192, 192, 1)'}
    }
    info = info_sensores.get(tipo_sensor)
    if not info:
        return "Sensor não encontrado", 404
    return render_template('grafico_individual.html', tipo_sensor=tipo_sensor, info=info)

# --- ROTAS DE API (sem alterações) ---

@app.route('/api/dados_historicos')
def api_dados_historicos():
    return jsonify(gerar_dados_historicos())

@app.route('/api/dados_atuais')
def api_dados_atuais():
    return jsonify(gerar_nova_leitura())



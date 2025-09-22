# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 9.0 - DASHBOARD COM GRÁFICOS INDIVIDUAIS)
#
#   - Dashboard principal continua com atualização em tempo real.
#   - Adiciona uma rota dinâmica (/grafico/<tipo_sensor>) para exibir gráficos individuais.
# ===================================================================================

import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- FUNÇÕES DE GERAÇÃO DE DADOS (sem alterações) ---

def gerar_dados_iniciais(device_id):
    dados_gerados = []
    hora_atual = datetime.now()
    for i in range(10):
        timestamp = hora_atual - timedelta(minutes=(9-i)*2)
        leitura = {
            "Horario": timestamp.strftime('%d/%m/%Y %H:%M:%S'),
            "Umidade": round(random.uniform(34.0, 36.0), 2),
            "Temperatura": round(random.uniform(20.0, 22.0), 2),
            "Chuva": round(random.uniform(0.0, 0.2), 2) if random.random() > 0.9 else 0.0
        }
        dados_gerados.append(leitura)
    return dados_gerados

def gerar_nova_leitura():
    timestamp = datetime.now()
    leitura = {
        "Horario": timestamp.strftime('%d/%m/%Y %H:%M:%S'),
        "Umidade": round(random.uniform(34.0, 36.0), 2),
        "Temperatura": round(random.uniform(20.0, 22.0), 2),
        "Chuva": round(random.uniform(0.0, 1.5), 2) if random.random() > 0.95 else 0.0
    }
    return leitura

def gerar_dados_historicos():
    dados_grafico = []
    hora_atual = datetime.now()
    for i in range(50):
        timestamp = hora_atual - timedelta(minutes=(49-i)*15)
        leitura = {
            "timestamp": timestamp.strftime('%H:%M'),
            "umidade": round(random.uniform(25.0, 45.0), 2),
            "temperatura": round(random.uniform(18.0, 30.0), 2),
            "chuva": round(random.uniform(0.0, 5.0), 2) if random.random() > 0.8 else 0.0
        }
        dados_grafico.append(leitura)
    return dados_grafico

# --- ROTAS DA NOSSA APLICAÇÃO ---

@app.route('/')
def pagina_de_acesso():
    return render_template('index.html')

@app.route('/dados', methods=['POST'])
def mostrar_dados():
    device_id = request.form['device_id']
    dados_iniciais = gerar_dados_iniciais(device_id)
    return render_template('dados.html', leituras=dados_iniciais, device_id=device_id)

@app.route('/api/dados_atuais')
def api_dados_atuais():
    return jsonify(gerar_nova_leitura())

@app.route('/api/dados_historicos')
def api_dados_historicos():
    return jsonify(gerar_dados_historicos())

# =======================================================================
# NOVO - ROTA DINÂMICA PARA GRÁFICOS INDIVIDUAIS
# =======================================================================
@app.route('/grafico/<tipo_sensor>')
def pagina_grafico_individual(tipo_sensor):
    """
    Renderiza a página de gráfico para um sensor específico.
    A variável <tipo_sensor> vem da URL (ex: /grafico/umidade).
    """
    # Define as propriedades de cada gráfico
    info_sensores = {
        'umidade': {'titulo': 'Análise Gráfica de Umidade do Solo (%)', 'cor': 'rgba(54, 162, 235, 1)'},
        'temperatura': {'titulo': 'Análise Gráfica de Temperatura do Solo (°C)', 'cor': 'rgba(255, 99, 132, 1)'},
        'chuva': {'titulo': 'Análise Gráfica de Precipitação (mm)', 'cor': 'rgba(75, 192, 192, 1)'}
    }

    # Pega as informações do sensor solicitado. Retorna um 404 se o sensor não existir.
    info = info_sensores.get(tipo_sensor)
    if not info:
        return "Sensor não encontrado", 404

    # Renderiza o template, passando o tipo do sensor e suas informações (título e cor)
    return render_template('grafico_individual.html', tipo_sensor=tipo_sensor, info=info)


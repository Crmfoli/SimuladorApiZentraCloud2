# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 9.5 - PÁGINAS SEPARADAS E DINÂMICAS)
#
#   - Dashboard principal com tabela em tempo real.
#   - Páginas de gráfico individuais que TAMBÉM se atualizam em tempo real.
# ===================================================================================

import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- FUNÇÕES DE GERAÇÃO DE DADOS ---

def gerar_dados_historicos(pontos=50):
    """Gera uma lista de dados históricos para popular os gráficos inicialmente."""
    dados = []
    hora_atual = datetime.now()
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
    timestamp = datetime.now()
    return {
        "timestamp_completo": timestamp.strftime('%d/%m/%Y %H:%M:%S'),
        "timestamp_grafico": timestamp.strftime('%H:%M:%S'),
        "umidade": round(random.uniform(30.0, 40.0), 2),
        "temperatura": round(random.uniform(20.0, 28.0), 2),
        "chuva": round(random.uniform(0.0, 2.0), 2) if random.random() > 0.95 else 0.0
    }

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def pagina_de_acesso():
    """Renderiza a página inicial com o formulário de login."""
    return render_template('index.html')

@app.route('/dados', methods=['POST'])
def mostrar_dados():
    """Renderiza a página do dashboard com a tabela."""
    device_id = request.form['device_id']
    # A tabela inicial não precisa de dados, pois o JS irá populá-la
    return render_template('dados.html', device_id=device_id)

@app.route('/grafico/<tipo_sensor>')
def pagina_grafico_individual(tipo_sensor):
    """Renderiza a página de gráfico para um sensor específico."""
    info_sensores = {
        'umidade': {'titulo': 'Umidade do Solo (%)', 'cor': 'rgba(54, 162, 235, 1)'},
        'temperatura': {'titulo': 'Temperatura do Solo (°C)', 'cor': 'rgba(255, 99, 132, 1)'},
        'chuva': {'titulo': 'Precipitação (mm)', 'cor': 'rgba(75, 192, 192, 1)'}
    }
    info = info_sensores.get(tipo_sensor)
    if not info:
        return "Sensor não encontrado", 404
    return render_template('grafico_individual.html', tipo_sensor=tipo_sensor, info=info)

# --- ROTAS DE API ---

@app.route('/api/dados_historicos')
def api_dados_historicos():
    """API que fornece a carga inicial de dados."""
    return jsonify(gerar_dados_historicos(pontos=30))

@app.route('/api/dados_atuais')
def api_dados_atuais():
    """API que fornece uma única leitura atualizada para o loop em tempo real."""
    return jsonify(gerar_nova_leitura())



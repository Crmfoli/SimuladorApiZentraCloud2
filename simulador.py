# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 8.0 - GRÁFICOS COM CHART.JS)
#
#   - Adiciona uma página de gráficos.
#   - Adiciona uma nova rota de API para fornecer dados históricos para os gráficos.
# ===================================================================================

import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def gerar_dados_iniciais(device_id):
    """Gera a primeira carga de dados para a tabela."""
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
    """Gera apenas UMA nova leitura de dados."""
    timestamp = datetime.now()
    leitura = {
        "Horario": timestamp.strftime('%d/%m/%Y %H:%M:%S'),
        "Umidade": round(random.uniform(34.0, 36.0), 2),
        "Temperatura": round(random.uniform(20.0, 22.0), 2),
        "Chuva": round(random.uniform(0.0, 1.5), 2) if random.random() > 0.95 else 0.0
    }
    return leitura

# =======================================================================
# NOVO - FUNÇÃO PARA GERAR DADOS PARA OS GRÁFICOS
# =======================================================================
def gerar_dados_historicos():
    """Gera uma lista maior de dados simulados para popular os gráficos."""
    dados_grafico = []
    hora_atual = datetime.now()
    # Vamos gerar 50 pontos de dados para o gráfico
    for i in range(50):
        # Gerando dados retroativos a cada 15 minutos
        timestamp = hora_atual - timedelta(minutes=(49-i)*15)
        leitura = {
            "timestamp": timestamp.strftime('%H:%M'), # Apenas Hora:Minuto para o eixo do gráfico
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
    nova_leitura = gerar_nova_leitura()
    return jsonify(nova_leitura)

# =======================================================================
# NOVO - ROTAS PARA A PÁGINA DE GRÁFICOS
# =======================================================================
@app.route('/graficos')
def pagina_de_graficos():
    """Renderiza a nova página HTML que conterá os gráficos."""
    # O device_id poderia ser passado aqui se necessário, mas para este exemplo não precisamos.
    return render_template('graficos.html')

@app.route('/api/dados_historicos')
def api_dados_historicos():
    """A nova API que fornece os dados para os gráficos em formato JSON."""
    dados = gerar_dados_historicos()
    return jsonify(dados)


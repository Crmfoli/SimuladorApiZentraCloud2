# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 6.0 - INTERFACE HTML COM FORMULÁRIO)
#
#   - Apresenta um formulário de login em HTML.
#   - Recebe os dados do formulário.
#   - Gera uma lista de dados simulados sob demanda.
#   - Apresenta os dados em uma nova página HTML com uma tabela.
# ===================================================================================

import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request # Novas importações!

# Cria a aplicação web
app = Flask(__name__)

def gerar_dados_simulados(device_id):
    """
    Gera uma lista de leituras de sensores para simular uma resposta de API.
    Não roda mais em loop, é chamada apenas uma vez.
    """
    dados_gerados = []
    hora_atual = datetime.now()

    # Vamos gerar 10 registros de dados para os últimos momentos
    for i in range(10):
        timestamp = hora_atual - timedelta(minutes=i*15) # Medições a cada 15 minutos
        umidade = round(random.uniform(34.0, 36.0), 2)
        temp_solo = round(random.uniform(20.0, 22.0), 2)
        precipitacao = round(random.uniform(0.0, 1.5), 2) if random.random() > 0.7 else 0.0

        leitura_plana = {
            "Horario": timestamp.strftime('%d/%m/%Y %H:%M:%S'),
            "Umidade": umidade,
            "Temperatura": temp_solo,
            "Chuva": precipitacao
        }
        dados_gerados.append(leitura_plana)
    
    return sorted(dados_gerados, key=lambda x: x['Horario']) # Ordena do mais antigo para o mais novo

# --- ROTAS DA NOSSA APLICAÇÃO ---

@app.route('/')
def pagina_de_acesso():
    """
    Esta função é chamada quando alguém acessa a URL principal.
    Ela simplesmente mostra a página do formulário de login.
    """
    return render_template('index.html')

@app.route('/dados', methods=['POST'])
def mostrar_dados():
    """
    Esta função é chamada quando o formulário da página inicial é enviado.
    Ela só aceita requisições do tipo POST.
    """
    # 1. Pega os dados que o usuário digitou no formulário
    username = request.form['username']
    api_token = request.form['api_token']
    device_id = request.form['device_id']

    # (Em um app real, aqui você validaria o username e api_token)
    
    # 2. Gera os dados simulados para o dispositivo solicitado
    dados_simulados = gerar_dados_simulados(device_id)

    # 3. Renderiza a página 'dados.html', passando a lista de dados para ela
    return render_template('dados.html', leituras=dados_simulados, device_id=device_id)

# O Gunicorn do Render vai se encarregar de rodar a aplicação.
# Não precisamos da thread ou do loop 'while True'.
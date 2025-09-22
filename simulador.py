# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 12.2 - CORREÇÃO DE RACE CONDITION DO DISCO)
#
#   - Adota a estratégia de "Lazy Initialization" para criar o arquivo de dados.
#   - O arquivo só é criado na primeira vez que os dados são lidos, evitando erros de timing.
# ===================================================================================

import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# --- CONFIGURAÇÃO (sem alterações) ---
TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")
DATA_DIR = "/data"
DATA_FILE = os.path.join(DATA_DIR, "dados_sensores.csv")

# --- FUNÇÕES DE MANIPULAÇÃO DE DADOS ---

def create_initial_data_file():
    """Cria o arquivo CSV com dados históricos. Esta função só é chamada se o arquivo não existir."""
    print(f"Arquivo de dados não encontrado. Criando novo em {DATA_FILE}...")
    
    hora_inicial = datetime.now(TZ_BRASILIA) - pd.DateOffset(months=3)
    timestamps = pd.to_datetime(pd.date_range(start=hora_inicial, end=datetime.now(TZ_BRASILIA), freq="1H"))
    
    dados = []
    for ts in timestamps:
        dados.append({
            "timestamp": ts,
            "umidade": round(random.uniform(20.0, 50.0), 2),
            "temperatura": round(random.uniform(15.0, 35.0), 2),
            "chuva": round(random.uniform(0.0, 5.0), 2) if random.random() > 0.8 else 0.0
        })
    
    df = pd.DataFrame(dados)
    df.to_csv(DATA_FILE, index=False)
    print("Arquivo de dados criado com sucesso.")

# =======================================================================
# ALTERAÇÃO CRÍTICA AQUI
# =======================================================================
def ler_dados_do_csv():
    """Lê o arquivo CSV. Se o arquivo não existir, chama a função para criá-lo primeiro."""
    # Esta verificação agora acontece aqui, sob demanda.
    if not os.path.exists(DATA_FILE):
        create_initial_data_file()

    if not os.path.exists(DATA_FILE):
        # Se mesmo após a tentativa de criação o arquivo não existir, retorna um DataFrame vazio.
        return pd.DataFrame()
        
    return pd.read_csv(DATA_FILE, parse_dates=['timestamp'])

def salvar_nova_leitura(leitura):
    """Adiciona uma nova linha de leitura ao final do arquivo CSV."""
    df_leitura = pd.DataFrame([leitura])
    df_leitura.to_csv(DATA_FILE, mode='a', header=False, index=False)


# --- ROTAS DA APLICAÇÃO (sem alterações) ---

@app.route('/')
def pagina_de_acesso():
    return render_template('index.html')

@app.route('/dashboard', methods=['POST'])
def pagina_dashboard():
    device_id = request.form['device_id']
    return render_template('dashboard.html', device_id=device_id)

# --- ROTAS DE API (sem alterações) ---

@app.route('/api/dados')
def api_dados():
    df = ler_dados_do_csv()
    if df.empty:
        return jsonify([])
    mes_selecionado = request.args.get('month')
    if mes_selecionado:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df_filtrado = df[df['timestamp'].dt.strftime('%Y-%m') == mes_selecionado]
    else:
        df_filtrado = df.tail(30)
    dados_formatados = []
    for _, row in df_filtrado.iterrows():
        dados_formatados.append({
            "timestamp_completo": row['timestamp'].strftime('%d/%m/%Y %H:%M:%S'),
            "timestamp_grafico": row['timestamp'].strftime('%H:%M:%S'),
            "umidade": row['umidade'],
            "temperatura": row['temperatura'],
            "chuva": row['chuva']
        })
    return jsonify(dados_formatados)


@app.route('/api/dados_atuais')
def api_dados_atuais():
    nova_leitura = {
        "timestamp": datetime.now(TZ_BRASILIA),
        "umidade": round(random.uniform(30.0, 40.0), 2),
        "temperatura": round(random.uniform(20.0, 28.0), 2),
        "chuva": round(random.uniform(0.0, 2.0), 2) if random.random() > 0.95 else 0.0
    }
    salvar_nova_leitura(nova_leitura)
    leitura_formatada = {
        "timestamp_completo": nova_leitura['timestamp'].strftime('%d/%m/%Y %H:%M:%S'),
        "timestamp_grafico": nova_leitura['timestamp'].strftime('%H:%M:%S'),
        **{k: v for k, v in nova_leitura.items() if k != 'timestamp'}
    }
    return jsonify(leitura_formatada)

@app.route('/api/meses_disponiveis')
def api_meses_disponiveis():
    df = ler_dados_do_csv()
    if df.empty:
        return jsonify([])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    meses = df['timestamp'].dt.strftime('%Y-%m').unique().tolist()
    meses.reverse()
    return jsonify(meses)

# =======================================================================
# REMOVIDO: A chamada de inicialização não acontece mais aqui no final.
# =======================================================================
# setup_initial_data()





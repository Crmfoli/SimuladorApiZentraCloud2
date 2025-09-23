# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 12.4 - VERSÃO FINAL ROBUSTA)
#
#   - Simplifica a geração de dados históricos para evitar falhas.
#   - Garante que todas as operações com arquivos e datas sejam seguras.
# ===================================================================================

import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo
import traceback

import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# --- CONFIGURAÇÃO ---
TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")
DATA_DIR = "/data"
DATA_FILE = os.path.join(DATA_DIR, "dados_sensores.csv")

# --- FUNÇÕES DE MANIPULAÇÃO DE DADOS ---

def create_initial_data_file():
    """Cria o arquivo CSV com dados históricos de forma segura."""
    try:
        print(f"Arquivo de dados não encontrado. Criando novo em {DATA_FILE}...")
        
        # Lógica de data simplificada e mais robusta
        end_date = datetime.now(TZ_BRASILIA)
        start_date = end_date - pd.DateOffset(months=3)
        
        # Usamos pd.Timestamp para garantir compatibilidade
        timestamps = pd.date_range(start=pd.Timestamp(start_date), end=pd.Timestamp(end_date), freq="h")
        
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
    except Exception as e:
        # Se qualquer coisa der errado aqui, veremos o erro detalhado nos logs do Render
        print("!!!!!!!!!!! FALHA CRÍTICA AO CRIAR ARQUIVO DE DADOS INICIAL !!!!!!!!!!!")
        print(traceback.format_exc())
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


def ler_dados_do_csv():
    """Lê o arquivo CSV. Se não existir, chama a função para criá-lo."""
    if not os.path.exists(DATA_FILE):
        create_initial_data_file()
    
    # Verifica novamente, pois a criação pode ter falhado
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()
        
    return pd.read_csv(DATA_FILE, parse_dates=['timestamp'])

def salvar_nova_leitura(leitura):
    """Adiciona uma nova linha ao arquivo CSV."""
    df_leitura = pd.DataFrame([leitura])
    df_leitura.to_csv(DATA_FILE, mode='a', header=False, index=False)

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def pagina_de_acesso():
    return render_template('index.html')

@app.route('/dashboard', methods=['POST'])
def pagina_dashboard():
    device_id = request.form['device_id']
    return render_template('dashboard.html', device_id=device_id)

# --- ROTAS DE API ---

@app.route('/api/dados')
def api_dados():
    try:
        df = ler_dados_do_csv()
        if df.empty: return jsonify([])
        mes_selecionado = request.args.get('month')
        if mes_selecionado:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df_filtrado = df[df['timestamp'].dt.strftime('%Y-%m') == mes_selecionado]
        else:
            df_filtrado = df.tail(30)
        
        # Converte o DataFrame filtrado para o formato JSON esperado
        dados_formatados = []
        for _, row in df_filtrado.iterrows():
            dados_formatados.append({
                "timestamp_completo": row['timestamp'].strftime('%d/%m/%Y %H:%M:%S'),
                "timestamp_grafico": row['timestamp'].strftime('%H:%M:%S'),
                "umidade": row['umidade'], "temperatura": row['temperatura'], "chuva": row['chuva']
            })
        return jsonify(dados_formatados)
    except Exception:
        print(f"Erro na rota /api/dados: {traceback.format_exc()}")
        return jsonify({"error": "Erro interno ao processar dados"}), 500

@app.route('/api/dados_atuais')
def api_dados_atuais():
    try:
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
            "umidade": nova_leitura['umidade'], "temperatura": nova_leitura['temperatura'], "chuva": nova_leitura['chuva']
        }
        return jsonify(leitura_formatada)
    except Exception:
        print(f"Erro na rota /api/dados_atuais: {traceback.format_exc()}")
        return jsonify({"error": "Erro interno ao gerar novo dado"}), 500

@app.route('/api/meses_disponiveis')
def api_meses_disponiveis():
    try:
        df = ler_dados_do_csv()
        if df.empty: return jsonify([])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        meses = df['timestamp'].dt.strftime('%Y-%m').unique().tolist()
        meses.reverse()
        return jsonify(meses)
    except Exception:
        print(f"Erro na rota /api/meses_disponiveis: {traceback.format_exc()}")
        return jsonify({"error": "Erro interno ao buscar meses"}), 500


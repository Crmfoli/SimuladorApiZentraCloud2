# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 15.0 - SIMULAÇÃO DE DADOS INTELIGENTE)
#
#   - Gera dados de forma dinâmica para simular ciclos de tempo (seca, chuva, saturação).
#   - Permite a visualização de todos os níveis de risco em um curto período.
# ===================================================================================

import os
import random
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, render_template, request
import pandas as pd
from sqlalchemy import create_engine, text, inspect

app = Flask(__name__)

# --- CONFIGURAÇÃO ---
TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# --- FUNÇÕES DE GERAÇÃO DE DADOS (REESCRITAS) ---

def gerar_leitura_baseada_no_tempo(timestamp):
    """Gera uma leitura de sensor com base no minuto do timestamp fornecido."""
    minuto = timestamp.minute

    umidade, temperatura, chuva = 0, 0, 0

    # CICLO DE TEMPO:
    # Minutos 0-19: Período de seca
    if 0 <= minuto < 20:
        # Umidade começa em 35% e cai para 20%
        umidade = 35.0 - (minuto * 0.75)
        temperatura = 25.0 + (minuto * 0.2) # Temperatura sobe um pouco
        chuva = 0.0
    # Minutos 20-39: Período de chuva intensa
    elif 20 <= minuto < 40:
        # Umidade sobe de 20% para 55%
        umidade = 20.0 + ((minuto - 20) * 1.75)
        temperatura = 29.0 - ((minuto - 20) * 0.3) # Temperatura cai com a chuva
        chuva = random.uniform(1.0, 5.0)
    # Minutos 40-59: Período pós-chuva (solo saturado)
    else:
        # Umidade começa em 55% e cai lentamente
        umidade = 55.0 - ((minuto - 40) * 1.0)
        temperatura = 23.0 + ((minuto - 40) * 0.1) # Temperatura se recupera devagar
        chuva = 0.0
    
    # Adiciona um pouco de variação aleatória para não ser uma linha perfeita
    umidade += random.uniform(-1.5, 1.5)
    temperatura += random.uniform(-1.0, 1.0)

    return {
        "timestamp": timestamp,
        "umidade": round(max(10, min(60, umidade)), 2), # Garante que os valores fiquem em uma faixa
        "temperatura": round(temperatura, 2),
        "chuva": round(chuva, 2)
    }

def create_initial_data_file():
    """Cria a tabela com dados históricos que seguem o ciclo de tempo."""
    try:
        print("Criando tabela com dados históricos inteligentes...")
        hora_atual = datetime.now(TZ_BRASILIA)
        total_horas = 30 * 24
        
        dados = []
        for i in range(total_horas):
            ts = hora_atual - timedelta(hours=i)
            leitura = gerar_leitura_baseada_no_tempo(ts)
            # Formata para inserção no banco de dados
            dados.append(f"('{leitura['timestamp']}', {leitura['umidade']}, {leitura['temperatura']}, {leitura['chuva']})")
        
        dados.reverse()
        values_sql = ", ".join(dados)
        
        with engine.connect() as connection:
            connection.execute(text("""CREATE TABLE leituras (id SERIAL PRIMARY KEY, timestamp TIMESTAMPTZ NOT NULL, umidade FLOAT NOT NULL, temperatura FLOAT NOT NULL, chuva FLOAT NOT NULL);"""))
            connection.execute(text(f"INSERT INTO leituras (timestamp, umidade, temperatura, chuva) VALUES {values_sql};"))
            connection.commit()
        print("Tabela criada com dados históricos inteligentes.")
    except Exception:
        print(f"FALHA CRÍTICA AO CRIAR TABELA: {traceback.format_exc()}")

def ler_dados_do_db():
    """Lê dados do banco, garantindo que a tabela exista."""
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            if not inspector.has_table('leituras'):
                create_initial_data_file()
            
            # Retorna o DataFrame lendo a tabela inteira
            return pd.read_sql_table('leituras', connection, parse_dates=['timestamp'])
    except Exception:
        print(f"Erro ao ler do banco de dados: {traceback.format_exc()}")
        return pd.DataFrame() # Retorna um DataFrame vazio em caso de erro

def salvar_nova_leitura_no_db(leitura):
    """Salva uma nova leitura no banco de dados."""
    with engine.connect() as connection:
        query = text("INSERT INTO leituras (timestamp, umidade, temperatura, chuva) VALUES (:ts, :u, :t, :c)")
        connection.execute(query, {"ts": leitura['timestamp'], "u": leitura['umidade'], "t": leitura['temperatura'], "c": leitura['chuva']})
        connection.commit()

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def pagina_de_acesso(): return render_template('index.html')

@app.route('/dashboard', methods=['POST'])
def pagina_dashboard():
    device_id = request.form['device_id']
    return render_template('dashboard.html', device_id=device_id)

# --- ROTAS DE API ---
@app.route('/api/dados')
def api_dados():
    try:
        df = ler_dados_do_db()
        # ... (Resto do código sem alterações)
        if df.empty: return jsonify([])
        mes_selecionado = request.args.get('month')
        if mes_selecionado:
            df_filtrado = df[df['timestamp'].dt.strftime('%Y-%m') == mes_selecionado]
        else:
            df_filtrado = df.tail(30)
        dados_formatados = df_filtrado.apply(lambda row: { "timestamp_completo": row['timestamp'].astimezone(TZ_BRASILIA).strftime('%d/%m/%Y %H:%M:%S'), "timestamp_grafico": row['timestamp'].astimezone(TZ_BRASILIA).strftime('%H:%M:%S'), "umidade": row['umidade'], "temperatura": row['temperatura'], "chuva": row['chuva'] }, axis=1).tolist()
        return jsonify(dados_formatados)
    except Exception:
        print(f"Erro na rota /api/dados: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

@app.route('/api/dados_atuais')
def api_dados_atuais():
    """Gera, SALVA e retorna uma nova leitura inteligente."""
    try:
        nova_leitura = gerar_leitura_baseada_no_tempo(datetime.now(TZ_BRASILIA))
        salvar_nova_leitura_no_db(nova_leitura)
        leitura_formatada = { "timestamp_completo": nova_leitura['timestamp'].strftime('%d/%m/%Y %H:%M:%S'), "timestamp_grafico": nova_leitura['timestamp'].strftime('%H:%M:%S'), "umidade": nova_leitura['umidade'], "temperatura": nova_leitura['temperatura'], "chuva": nova_leitura['chuva'] }
        return jsonify(leitura_formatada)
    except Exception:
        print(f"Erro na rota /api/dados_atuais: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

@app.route('/api/meses_disponiveis')
def api_meses_disponiveis():
    try:
        df = ler_dados_do_db()
        if df.empty: return jsonify([])
        meses = df['timestamp'].dt.strftime('%Y-%m').unique().tolist()
        meses.reverse()
        return jsonify(meses)
    except Exception:
        print(f"Erro na rota /api/meses_disponiveis: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500


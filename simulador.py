# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 15.1 - FOCO EM RISCO DE DESLIZAMENTO)
#
#   - Aumenta a intensidade da chuva simulada para testar os limites da análise de risco.
# ===================================================================================

import os
import random
import traceback
from datetime import datetime, timedelta
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
    if 0 <= minuto < 20: # Período de seca
        umidade = 35.0 - (minuto * 0.75)
        temperatura = 25.0 + (minuto * 0.2)
        chuva = 0.0
    elif 20 <= minuto < 40: # Período de chuva intensa
        umidade = 20.0 + ((minuto - 20) * 2.0) # Umidade sobe mais rápido
        temperatura = 29.0 - ((minuto - 20) * 0.3)
        # ALTERAÇÃO PRINCIPAL: Chuva muito mais forte (valores em mm/hora)
        chuva = random.uniform(5.0, 25.0) 
    else: # Período pós-chuva (solo saturado)
        umidade = 60.0 - ((minuto - 40) * 1.0) # Começa de um ponto mais alto
        temperatura = 23.0 + ((minuto - 40) * 0.1)
        chuva = 0.0
    
    umidade += random.uniform(-1.5, 1.5)
    temperatura += random.uniform(-1.0, 1.0)

    return {
        "timestamp": timestamp,
        "umidade": round(max(10, min(70, umidade)), 2), # Aumentado o limite máximo
        "temperatura": round(temperatura, 2),
        "chuva": round(chuva, 2)
    }

# O restante do arquivo Python permanece o mesmo da versão anterior.
# Para garantir, aqui está o código completo.

def create_initial_data_file():
    try:
        print("Criando tabela com dados históricos inteligentes...")
        hora_atual = datetime.now(TZ_BRASILIA)
        total_horas = 30 * 24
        dados = []
        for i in range(total_horas):
            ts = hora_atual - timedelta(hours=i)
            leitura = gerar_leitura_baseada_no_tempo(ts)
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
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            if not inspector.has_table('leituras'):
                create_initial_data_file()
            return pd.read_sql_table('leituras', connection, parse_dates=['timestamp'])
    except Exception:
        print(f"Erro ao ler do banco de dados: {traceback.format_exc()}"); return pd.DataFrame()

def salvar_nova_leitura_no_db(leitura):
    with engine.connect() as connection:
        query = text("INSERT INTO leituras (timestamp, umidade, temperatura, chuva) VALUES (:ts, :u, :t, :c)")
        connection.execute(query, {"ts": leitura['timestamp'], "u": leitura['umidade'], "t": leitura['temperatura'], "c": leitura['chuva']})
        connection.commit()

@app.route('/')
def pagina_de_acesso(): return render_template('index.html')

@app.route('/dashboard', methods=['POST'])
def pagina_dashboard():
    device_id = request.form['device_id']
    return render_template('dashboard.html', device_id=device_id)

@app.route('/api/dados')
def api_dados():
    try:
        df = ler_dados_do_db()
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



# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 17.1 - LEGENDA DINÂMICA NO MAPA)
#
#   - Adiciona uma nova rota de API (/api/status_sensores) para a legenda.
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

# --- FUNÇÕES DE MANIPULAÇÃO DE DADOS (sem alterações) ---
def gerar_leitura_baseada_no_tempo(timestamp):
    minuto = timestamp.minute; umidade, temperatura, chuva = 0, 0, 0
    if 0 <= minuto < 20: umidade = 35.0 - (minuto * 0.75); temperatura = 25.0 + (minuto * 0.2); chuva = 0.0
    elif 20 <= minuto < 40: umidade = 20.0 + ((minuto - 20) * 2.0); temperatura = 29.0 - ((minuto - 20) * 0.3); chuva = random.uniform(5.0, 25.0)
    else: umidade = 60.0 - ((minuto - 40) * 1.0); temperatura = 23.0 + ((minuto - 40) * 0.1); chuva = 0.0
    umidade += random.uniform(-1.5, 1.5); temperatura += random.uniform(-1.0, 1.0)
    return { "timestamp": timestamp, "umidade": round(max(10, min(70, umidade)), 2), "temperatura": round(temperatura, 2), "chuva": round(chuva, 2) }

# ... (outras funções de dados como create_initial_data_file, ler_dados_do_db, etc. permanecem aqui) ...
def create_initial_data_file(connection):
    try:
        print("Criando tabela com dados históricos..."); hora_atual = datetime.now(TZ_BRASILIA); total_horas = 30 * 24; dados = []
        for i in range(total_horas):
            leitura = gerar_leitura_baseada_no_tempo(hora_atual - timedelta(hours=i))
            dados.append(f"('{leitura['timestamp']}', {leitura['umidade']}, {leitura['temperatura']}, {leitura['chuva']})")
        dados.reverse(); values_sql = ", ".join(dados)
        connection.execute(text("""CREATE TABLE leituras (id SERIAL PRIMARY KEY, timestamp TIMESTAMPTZ NOT NULL, umidade FLOAT NOT NULL, temperatura FLOAT NOT NULL, chuva FLOAT NOT NULL);"""))
        connection.execute(text(f"INSERT INTO leituras (timestamp, umidade, temperatura, chuva) VALUES {values_sql};")); connection.commit()
        print("Tabela criada com sucesso.")
    except Exception: print(f"FALHA CRÍTICA AO CRIAR TABELA: {traceback.format_exc()}")
def ensure_table_exists(connection):
    inspector = inspect(connection)
    if not inspector.has_table('leituras'): create_initial_data_file(connection)
def ler_dados_do_db():
    try:
        with engine.connect() as connection:
            ensure_table_exists(connection)
            return pd.read_sql_table('leituras', connection, parse_dates=['timestamp'])
    except Exception: print(f"Erro ao ler do banco de dados: {traceback.format_exc()}"); return pd.DataFrame()
def salvar_nova_leitura_no_db(leitura):
    with engine.connect() as connection:
        ensure_table_exists(connection)
        query = text("INSERT INTO leituras (timestamp, umidade, temperatura, chuva) VALUES (:ts, :u, :t, :c)"); connection.execute(query, {"ts": leitura['timestamp'], "u": leitura['umidade'], "t": leitura['temperatura'], "c": leitura['chuva']}); connection.commit()

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def pagina_de_acesso(): return render_template('index.html')

@app.route('/mapa', methods=['GET', 'POST'])
def pagina_mapa(): return render_template('mapa.html')

@app.route('/dashboard')
def pagina_dashboard():
    device_id = request.args.get('device_id', 'SN-A7B4')
    return render_template('dashboard.html', device_id=device_id)

# --- ROTAS DE API ---

@app.route('/api/dados')
def api_dados():
    # ... (código existente, sem alterações)
    try:
        df = ler_dados_do_db();
        if df.empty: return jsonify([])
        mes_selecionado = request.args.get('month')
        if mes_selecionado: df_filtrado = df[df['timestamp'].dt.strftime('%Y-%m') == mes_selecionado]
        else: df_filtrado = df.tail(30)
        dados_formatados = df_filtrado.apply(lambda row: { "timestamp_completo": row['timestamp'].astimezone(TZ_BRASILIA).strftime('%d/%m/%Y %H:%M:%S'), "timestamp_grafico": row['timestamp'].astimezone(TZ_BRASILIA).strftime('%H:%M:%S'), "umidade": row['umidade'], "temperatura": row['temperatura'], "chuva": row['chuva'] }, axis=1).tolist()
        return jsonify(dados_formatados)
    except Exception: print(f"Erro na rota /api/dados: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

@app.route('/api/dados_atuais')
def api_dados_atuais():
    # ... (código existente, sem alterações)
    try:
        nova_leitura = gerar_leitura_baseada_no_tempo(datetime.now(TZ_BRASILIA))
        salvar_nova_leitura_no_db(nova_leitura)
        leitura_formatada = { "timestamp_completo": nova_leitura['timestamp'].strftime('%d/%m/%Y %H:%M:%S'), "timestamp_grafico": nova_leitura['timestamp'].strftime('%H:%M:%S'), "umidade": nova_leitura['umidade'], "temperatura": nova_leitura['temperatura'], "chuva": nova_leitura['chuva'] }
        return jsonify(leitura_formatada)
    except Exception: print(f"Erro na rota /api/dados_atuais: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

@app.route('/api/meses_disponiveis')
def api_meses_disponiveis():
    # ... (código existente, sem alterações)
    try:
        df = ler_dados_do_db()
        if df.empty: return jsonify([])
        meses = df['timestamp'].dt.strftime('%Y-%m').unique().tolist()
        meses.reverse()
        return jsonify(meses)
    except Exception: print(f"Erro na rota /api/meses_disponiveis: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

# =======================================================================
# NOVA ROTA DE API PARA A LEGENDA
# =======================================================================
@app.route('/api/status_sensores')
def api_status_sensores():
    """Retorna a leitura de 'clima' atual para a análise de risco."""
    try:
        # Na nossa simulação, todos os sensores compartilham o mesmo "clima"
        leitura_atual = gerar_leitura_baseada_no_tempo(datetime.now(TZ_BRASILIA))
        status = { "umidade": leitura_atual['umidade'], "chuva": leitura_atual['chuva'] }
        return jsonify(status)
    except Exception:
        print(f"Erro na rota /api/status_sensores: {traceback.format_exc()}")
        return jsonify({"error": "Erro interno ao buscar status"}), 500

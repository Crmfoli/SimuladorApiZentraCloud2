# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 14.1 - FINAL À PROVA DE FALHAS)
#
#   - Elimina a "race condition" garantindo que a tabela exista antes de qualquer operação.
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

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def ensure_table_exists(connection):
    """Verifica se a tabela 'leituras' existe e a cria se necessário."""
    inspector = inspect(connection)
    if not inspector.has_table('leituras'):
        print("Tabela 'leituras' não encontrada. Criando e populando com dados históricos...")
        connection.execute(text("""
            CREATE TABLE leituras (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                umidade FLOAT NOT NULL,
                temperatura FLOAT NOT NULL,
                chuva FLOAT NOT NULL
            );
        """))
        
        hora_atual = datetime.now(TZ_BRASILIA)
        total_horas = 30 * 24
        dados = []
        for i in range(total_horas):
            ts = hora_atual - timedelta(hours=i)
            dados.append(f"('{ts}', {round(random.uniform(20.0, 50.0), 2)}, {round(random.uniform(15.0, 35.0), 2)}, {round(random.uniform(0.0, 5.0), 2) if random.random() > 0.8 else 0.0})")
        
        if dados:
            dados.reverse()
            values_sql = ", ".join(dados)
            connection.execute(text(f"INSERT INTO leituras (timestamp, umidade, temperatura, chuva) VALUES {values_sql};"))
        
        # connection.commit() é chamado automaticamente pelo 'with engine.connect()'
        print("Tabela 'leituras' criada e populada com sucesso.")

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
        with engine.connect() as connection:
            ensure_table_exists(connection) # Garante que a tabela existe antes de continuar
            
            mes_selecionado = request.args.get('month')
            if mes_selecionado:
                query = text("SELECT * FROM leituras WHERE to_char(timestamp, 'YYYY-MM') = :mes ORDER BY timestamp")
                result = connection.execute(query, {"mes": mes_selecionado}).mappings().all()
            else:
                query = text("SELECT * FROM leituras ORDER BY timestamp DESC LIMIT 30")
                result = connection.execute(query).mappings().all()
                result.reverse()

            dados_formatados = [{
                "timestamp_completo": row['timestamp'].astimezone(TZ_BRASILIA).strftime('%d/%m/%Y %H:%M:%S'),
                "timestamp_grafico": row['timestamp'].astimezone(TZ_BRASILIA).strftime('%H:%M:%S'),
                "umidade": row['umidade'], "temperatura": row['temperatura'], "chuva": row['chuva']
            } for row in result]
            return jsonify(dados_formatados)
    except Exception:
        print(f"Erro na rota /api/dados: {traceback.format_exc()}")
        return jsonify({"error": "Erro interno ao processar dados"}), 500

@app.route('/api/dados_atuais')
def api_dados_atuais():
    try:
        nova_leitura = { "timestamp": datetime.now(TZ_BRASILIA), "umidade": round(random.uniform(30.0, 40.0), 2), "temperatura": round(random.uniform(20.0, 28.0), 2), "chuva": round(random.uniform(0.0, 2.0), 2) if random.random() > 0.95 else 0.0 }
        with engine.connect() as connection:
            ensure_table_exists(connection) # Garante que a tabela existe
            query = text("INSERT INTO leituras (timestamp, umidade, temperatura, chuva) VALUES (:ts, :u, :t, :c)")
            connection.execute(query, {"ts": nova_leitura['timestamp'], "u": nova_leitura['umidade'], "t": nova_leitura['temperatura'], "c": nova_leitura['chuva']})
            connection.commit()
        return jsonify({ "timestamp_completo": nova_leitura['timestamp'].strftime('%d/%m/%Y %H:%M:%S'), "timestamp_grafico": nova_leitura['timestamp'].strftime('%H:%M:%S'), "umidade": nova_leitura['umidade'], "temperatura": nova_leitura['temperatura'], "chuva": nova_leitura['chuva'] })
    except Exception:
        print(f"Erro na rota /api/dados_atuais: {traceback.format_exc()}")
        return jsonify({"error": "Erro interno ao gerar novo dado"}), 500

@app.route('/api/meses_disponiveis')
def api_meses_disponiveis():
    try:
        with engine.connect() as connection:
            ensure_table_exists(connection) # Garante que a tabela existe
            query = text("SELECT DISTINCT to_char(timestamp, 'YYYY-MM') as mes FROM leituras ORDER BY mes DESC")
            result = connection.execute(query).mappings().all()
            meses = [row['mes'] for row in result]
            return jsonify(meses)
    except Exception:
        print(f"Erro na rota /api/meses_disponiveis: {traceback.format_exc()}")
        return jsonify({"error": "Erro interno ao buscar meses"}), 500

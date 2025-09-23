# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 14.0 - BANCO DE DADOS PROFISSIONAL COM POSTGRESQL)
#
#   - Usa um banco de dados PostgreSQL real para persistência de dados.
#   - Interage com o banco de dados usando SQLAlchemy.
# ===================================================================================

import os
import random
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, render_template, request
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text

app = Flask(__name__)

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")
# Pega a URL do banco de dados das variáveis de ambiente que configuramos no Render
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def setup_initial_data():
    """Verifica se a tabela de dados existe e a cria com dados históricos se necessário."""
    try:
        with engine.connect() as connection:
            # Verifica se a tabela já existe
            table_exists = connection.execute(text("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename  = 'leituras');")).scalar()
            
            if not table_exists:
                print("Tabela 'leituras' não encontrada. Criando e populando com dados históricos...")
                # Cria a tabela
                connection.execute(text("""
                    CREATE TABLE leituras (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ NOT NULL,
                        umidade FLOAT NOT NULL,
                        temperatura FLOAT NOT NULL,
                        chuva FLOAT NOT NULL
                    );
                """))
                
                # Gera dados históricos
                hora_atual = datetime.now(TZ_BRASILIA)
                total_horas = 30 * 24  # 30 dias
                dados = []
                for i in range(total_horas):
                    ts = hora_atual - timedelta(hours=i)
                    dados.append(f"('{ts}', {round(random.uniform(20.0, 50.0), 2)}, {round(random.uniform(15.0, 35.0), 2)}, {round(random.uniform(0.0, 5.0), 2) if random.random() > 0.8 else 0.0})")
                
                # Insere todos os dados de uma vez (muito mais eficiente)
                if dados:
                    dados.reverse() # Garante a ordem cronológica
                    values_sql = ", ".join(dados)
                    connection.execute(text(f"INSERT INTO leituras (timestamp, umidade, temperatura, chuva) VALUES {values_sql};"))
                
                connection.commit()
                print("Tabela 'leituras' criada e populada com sucesso.")

    except Exception as e:
        print(f"!!!!!!!!!!! FALHA CRÍTICA NO SETUP DO BANCO DE DADOS !!!!!!!!!!!\n{e}")

# --- ROTAS DA APLICAÇÃO (sem alterações no comportamento) ---
@app.route('/')
def pagina_de_acesso(): return render_template('index.html')

@app.route('/dashboard', methods=['POST'])
def pagina_dashboard():
    device_id = request.form['device_id']
    return render_template('dashboard.html', device_id=device_id)

# --- ROTAS DE API (agora leem do banco de dados) ---
@app.route('/api/dados')
def api_dados():
    try:
        with engine.connect() as connection:
            mes_selecionado = request.args.get('month')
            if mes_selecionado:
                # Filtra por mês usando SQL
                query = text("SELECT * FROM leituras WHERE to_char(timestamp, 'YYYY-MM') = :mes ORDER BY timestamp")
                result = connection.execute(query, {"mes": mes_selecionado}).fetchall()
            else:
                # Pega os 30 registros mais recentes
                query = text("SELECT * FROM leituras ORDER BY timestamp DESC LIMIT 30")
                result = connection.execute(query).fetchall()
                result.reverse()

            dados_formatados = [{
                "timestamp_completo": row[1].astimezone(TZ_BRASILIA).strftime('%d/%m/%Y %H:%M:%S'),
                "timestamp_grafico": row[1].astimezone(TZ_BRASILIA).strftime('%H:%M:%S'),
                "umidade": row[2], "temperatura": row[3], "chuva": row[4]
            } for row in result]
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
        # Salva a nova leitura no banco de dados
        with engine.connect() as connection:
            query = text("INSERT INTO leituras (timestamp, umidade, temperatura, chuva) VALUES (:ts, :u, :t, :c)")
            connection.execute(query, {"ts": nova_leitura['timestamp'], "u": nova_leitura['umidade'], "t": nova_leitura['temperatura'], "c": nova_leitura['chuva']})
            connection.commit()

        return jsonify({
            "timestamp_completo": nova_leitura['timestamp'].strftime('%d/%m/%Y %H:%M:%S'),
            "timestamp_grafico": nova_leitura['timestamp'].strftime('%H:%M:%S'),
            "umidade": nova_leitura['umidade'], "temperatura": nova_leitura['temperatura'], "chuva": nova_leitura['chuva']
        })
    except Exception:
        print(f"Erro na rota /api/dados_atuais: {traceback.format_exc()}")
        return jsonify({"error": "Erro interno ao gerar novo dado"}), 500

@app.route('/api/meses_disponiveis')
def api_meses_disponiveis():
    try:
        with engine.connect() as connection:
            # Query SQL para pegar os meses únicos que têm dados
            query = text("SELECT DISTINCT to_char(timestamp, 'YYYY-MM') as mes FROM leituras ORDER BY mes DESC")
            result = connection.execute(query).fetchall()
            meses = [row[0] for row in result]
            return jsonify(meses)
    except Exception:
        print(f"Erro na rota /api/meses_disponiveis: {traceback.format_exc()}")
        return jsonify({"error": "Erro interno ao buscar meses"}), 500

# --- INICIALIZAÇÃO ---
# Garante que a tabela no banco de dados exista ao iniciar a aplicação
setup_initial_data()

# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 12.0 - PERSISTÊNCIA DE DADOS COM CSV)
#
#   - Salva todas as leituras em um arquivo CSV em um disco persistente.
#   - Permite filtrar e visualizar os dados por mês.
# ===================================================================================

import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# --- CONFIGURAÇÃO ---
TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")
# O caminho para o nosso arquivo de dados, dentro do disco persistente do Render
DATA_DIR = "/data"
DATA_FILE = os.path.join(DATA_DIR, "dados_sensores.csv")

# --- FUNÇÕES DE MANIPULAÇÃO DE DADOS ---

def setup_initial_data():
    """Cria o arquivo CSV com dados históricos se ele não existir."""
    if not os.path.exists(DATA_FILE):
        print(f"Arquivo de dados não encontrado. Criando novo em {DATA_FILE}...")
        os.makedirs(DATA_DIR, exist_ok=True)
        # Gera 3 meses de dados históricos para popular o arquivo
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

def ler_dados_do_csv():
    """Lê o arquivo CSV e retorna um DataFrame do Pandas."""
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()
    # parse_dates=['timestamp'] converte a coluna de texto de volta para um objeto de data
    return pd.read_csv(DATA_FILE, parse_dates=['timestamp'])

def salvar_nova_leitura(leitura):
    """Adiciona uma nova linha de leitura ao final do arquivo CSV."""
    df_leitura = pd.DataFrame([leitura])
    # Escreve no CSV sem o cabeçalho (mode='a' para 'append')
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
    """API principal. Filtra dados por mês e retorna em formato para gráficos e tabela."""
    df = ler_dados_do_csv()
    if df.empty:
        return jsonify([])

    # Pega o parâmetro 'month' da URL (ex: ?month=2025-09)
    mes_selecionado = request.args.get('month')
    
    # Se um mês foi selecionado, filtra o DataFrame
    if mes_selecionado:
        # Garante que a coluna timestamp é do tipo datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Filtra pelo mês e ano (formato 'YYYY-MM')
        df_filtrado = df[df['timestamp'].dt.strftime('%Y-%m') == mes_selecionado]
    else:
        # Se nenhum mês for selecionado, retorna os últimos 30 pontos
        df_filtrado = df.tail(30)

    # Formata os dados para a resposta JSON
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
    """Gera, SALVA e retorna uma nova leitura."""
    nova_leitura = {
        "timestamp": datetime.now(TZ_BRASILIA),
        "umidade": round(random.uniform(30.0, 40.0), 2),
        "temperatura": round(random.uniform(20.0, 28.0), 2),
        "chuva": round(random.uniform(0.0, 2.0), 2) if random.random() > 0.95 else 0.0
    }
    salvar_nova_leitura(nova_leitura)
    
    # Formata para o frontend
    leitura_formatada = {
        "timestamp_completo": nova_leitura['timestamp'].strftime('%d/%m/%Y %H:%M:%S'),
        "timestamp_grafico": nova_leitura['timestamp'].strftime('%H:%M:%S'),
        **{k: v for k, v in nova_leitura.items() if k != 'timestamp'}
    }
    return jsonify(leitura_formatada)

@app.route('/api/meses_disponiveis')
def api_meses_disponiveis():
    """Retorna uma lista de meses (formato 'YYYY-MM') que possuem dados."""
    df = ler_dados_do_csv()
    if df.empty:
        return jsonify([])
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    # Cria uma coluna 'mes_ano', pega os valores únicos e reverte a ordem
    meses = df['timestamp'].dt.strftime('%Y-%m').unique().tolist()
    meses.reverse()
    return jsonify(meses)

# --- INICIALIZAÇÃO ---
# Garante que o arquivo de dados exista ao iniciar a aplicação
setup_initial_data()



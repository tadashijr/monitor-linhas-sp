import os
import json
import requests
from datetime import datetime
import pytz
from typing import Dict, List, Any, Optional
from flask import Flask, request
import threading
import time
# Chame esta função antes de app.run()
if __name__ == "__main__":
    print(f"🚇 Bot iniciando - {get_sp_time()}")
    setup_webhook()  # <-- Adicione esta linha
    app.run(host='0.0.0.0', port=PORT)

# Configurações
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
WEBSITES_JSON = os.environ.get('WEBSITES')
ALERTAR_FALHA = os.environ.get('ALERTAR_FALHA', 'false').lower() == 'true'
PORT = int(os.environ.get('PORT', 10000))  # Render usa PORT

# URL do site
SITE_URL = "https://ccm.artesp.sp.gov.br/metroferroviario/status-linhas/"
TIMEOUT = 30

# Todas as linhas disponíveis
TODAS_LINHAS = {
    "1": {"nome": "Linha 1-Azul", "operadora": "Metrô"},
    "2": {"nome": "Linha 2-Verde", "operadora": "Metrô"},
    "3": {"nome": "Linha 3-Vermelha", "operadora": "Metrô"},
    "4": {"nome": "Linha 4-Amarela", "operadora": "ViaQuatro"},
    "5": {"nome": "Linha 5-Lilás", "operadora": "ViaMobilidade"},
    "7": {"nome": "Linha 7-Rubi", "operadora": "CPTM"},
    "8": {"nome": "Linha 8-Diamante", "operadora": "ViaMobilidade"},
    "9": {"nome": "Linha 9-Esmeralda", "operadora": "ViaMobilidade"},
    "10": {"nome": "Linha 10-Turquesa", "operadora": "CPTM"},
    "11": {"nome": "Linha 11-Coral", "operadora": "CPTM"},
    "12": {"nome": "Linha 12-Safira", "operadora": "CPTM"},
    "13": {"nome": "Linha 13-Jade", "operadora": "CPTM"},
    "15": {"nome": "Linha 15-Prata", "operadora": "Metrô"}
}

app = Flask(__name__)

def get_sp_time() -> str:
    """Retorna a data/hora atual no fuso de São Paulo"""
    fuso_sp = pytz.timezone('America/Sao_Paulo')
    agora_utc = datetime.now(pytz.UTC)
    agora_sp = agora_utc.astimezone(fuso_sp)
    return agora_sp.strftime("%d/%m/%Y %H:%M:%S")

def send_telegram_message(chat_id: str, message: str) -> bool:
    """Envia mensagem para o Telegram"""
    if not TELEGRAM_TOKEN:
        print("❌ Erro: TELEGRAM_TOKEN não configurado")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, data=data, timeout=15)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {str(e)}")
        return False

def extrair_status_linha(html_content: str, nome_linha: str) -> Dict[str, Any]:
    """Extrai o status de uma linha específica do HTML"""
    resultado = {
        'status': '❓ Não encontrado',
        'detalhes': '',
        'success': False
    }
    
    try:
        if nome_linha in html_content:
            index = html_content.find(nome_linha)
            contexto = html_content[index:index + 500]
            
            if "Operação Normal" in contexto:
                resultado['status'] = "✅ Operação Normal"
                resultado['success'] = True
            elif "Operação Encerrada" in contexto:
                resultado['status'] = "🟡 Operação Encerrada"
                resultado['detalhes'] = "Linha fora de operação"
            elif "Velocidade Reduzida" in contexto:
                resultado['status'] = "🟠 Velocidade Reduzida"
                resultado['detalhes'] = "Operação com lentidão"
            elif "Paralisada" in contexto:
                resultado['status'] = "🔴 Paralisada"
                resultado['detalhes'] = "Linha paralisada"
    except Exception as e:
        resultado['detalhes'] = str(e)[:50]
    
    return resultado

def verificar_linha_especifica(linha_id: str) -> Optional[Dict[str, Any]]:
    """Verifica uma linha específica"""
    if linha_id not in TODAS_LINHAS:
        return None
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(SITE_URL, timeout=TIMEOUT, headers=headers)
        
        if response.status_code == 200:
            html = response.text
            linha_info = TODAS_LINHAS[linha_id]
            status_info = extrair_status_linha(html, linha_info['nome'])
            
            return {
                'id': linha_id,
                'nome': linha_info['nome'],
                'operadora': linha_info['operadora'],
                'status': status_info['status'],
                'success': status_info['success'],
                'detalhes': status_info['detalhes']
            }
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    return None

def verificar_todas_linhas() -> List[Dict[str, Any]]:
    """Verifica todas as linhas"""
    resultados = []
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(SITE_URL, timeout=TIMEOUT, headers=headers)
        
        if response.status_code == 200:
            html = response.text
            
            for linha_id, linha_info in TODAS_LINHAS.items():
                status_info = extrair_status_linha(html, linha_info['nome'])
                resultados.append({
                    'id': linha_id,
                    'nome': linha_info['nome'],
                    'operadora': linha_info['operadora'],
                    'status': status_info['status'],
                    'success': status_info['success'],
                    'detalhes': status_info['detalhes']
                })
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    return resultados

@app.route(f'/webhook/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    """Recebe atualizações do Telegram"""
    update = request.get_json()
    
    if 'message' in update and 'text' in update['message']:
        chat_id = str(update['message']['chat']['id'])
        text = update['message']['text'].strip()
        
        print(f"📩 Mensagem: {text}")
        
        if text == '/start':
            mensagem = """
🚇 *Bem-vindo ao Monitor Linhas SP!*

📋 *COMANDOS:*
/start - Esta mensagem
/linha [número] - Status de uma linha
  Ex: `/linha 2`
/todas - Status de TODAS as linhas

🤖 Notificações automáticas: 7h, 17h e 22h
"""
            send_telegram_message(chat_id, mensagem)
            
        elif text == '/todas':
            send_telegram_message(chat_id, "🔍 Consultando...")
            resultados = verificar_todas_linhas()
            
            if resultados:
                now = get_sp_time()
                msg = f"🚇 *Todas as Linhas - {now}*\n\n"
                
                for r in resultados:
                    msg += f"• *{r['nome']}*: {r['status']}\n"
                
                send_telegram_message(chat_id, msg)
            else:
                send_telegram_message(chat_id, "❌ Erro na consulta")
                
        elif text.startswith('/linha'):
            partes = text.split(' ', 1)
            if len(partes) > 1:
                linha_id = partes[1].strip()
                resultado = verificar_linha_especifica(linha_id)
                
                if resultado:
                    msg = f"🚇 *{resultado['nome']}*\n\n"
                    msg += f"📊 Status: {resultado['status']}\n"
                    if resultado['detalhes']:
                        msg += f"ℹ️ {resultado['detalhes']}\n"
                    send_telegram_message(chat_id, msg)
                else:
                    msg = "❌ Linha inválida. Use: 1,2,3,4,5,7,8,9,10,11,12,13,15"
                    send_telegram_message(chat_id, msg)
    
    return 'OK', 200

@app.route('/healthz')
def health():
    """Endpoint de saúde para o Render"""
    return 'OK', 200

@app.route('/')
def index():
    return 'Bot Monitor Linhas SP está rodando!', 200

def setup_webhook():
    """Configura o webhook no Telegram"""
    render_url = os.environ.get('RENDER_EXTERNAL_URL')
    if render_url:
        webhook_url = f"{render_url}/webhook/{TELEGRAM_TOKEN}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        
        try:
            response = requests.post(url, json={'url': webhook_url})
            if response.status_code == 200:
                print(f"✅ Webhook configurado: {webhook_url}")
            else:
                print(f"❌ Erro webhook: {response.text}")
        except Exception as e:
            print(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    print(f"🚇 Bot iniciando - {get_sp_time()}")
    setup_webhook()
    app.run(host='0.0.0.0', port=PORT)

def setup_webhook():
    """Configura o webhook automaticamente ao iniciar"""
    render_url = os.environ.get('RENDER_EXTERNAL_URL')
    if not render_url:
        # Tenta descobrir a URL do Render
        render_url = f"https://{os.environ.get('RENDER_SERVICE_NAME')}.onrender.com"
    
    if render_url and TELEGRAM_TOKEN:
        webhook_url = f"{render_url}/webhook/{TELEGRAM_TOKEN}"
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        
        try:
            response = requests.post(api_url, json={'url': webhook_url})
            if response.status_code == 200:
                print(f"✅ Webhook configurado: {webhook_url}")
                return True
            else:
                print(f"❌ Erro: {response.text}")
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
    
    return False

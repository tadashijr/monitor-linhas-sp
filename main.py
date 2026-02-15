import os
import json
import requests
from datetime import datetime
import pytz
from typing import Dict, List, Any, Optional
import time
from flask import Flask, request
import threading

# Configurações
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
WEBSITES_JSON = os.environ.get('WEBSITES')
ALERTAR_FALHA = os.environ.get('ALERTAR_FALHA', 'false').lower() == 'true'

# Timeout para requisições
TIMEOUT = 30
# URL do site
SITE_URL = "https://ccm.artesp.sp.gov.br/metroferroviario/status-linhas/"

# Todas as linhas disponíveis para monitoramento
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
    
    if len(message) > 4000:
        message = message[:4000] + "...\n\n(mensagem truncada)"
    
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, data=data, timeout=15)
        if response.status_code == 200:
            print(f"✅ Mensagem enviada para chat {chat_id}")
            return True
        else:
            print(f"❌ Erro na API do Telegram: {response.status_code}")
            return False
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
            else:
                resultado['status'] = "⚠️ Status desconhecido"
        else:
            resultado['status'] = "❌ Linha não encontrada no site"
            
    except Exception as e:
        resultado['status'] = f"❌ Erro na extração"
        resultado['detalhes'] = str(e)[:50]
    
    return resultado

def verificar_todas_linhas() -> List[Dict[str, Any]]:
    """Verifica todas as linhas disponíveis no site"""
    resultados = []
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
        print(f"❌ Erro ao acessar site: {str(e)}")
    
    return resultados

def verificar_linha_especifica(linha_id: str) -> Optional[Dict[str, Any]]:
    """Verifica uma linha específica"""
    if linha_id not in TODAS_LINHAS:
        return None
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
        print(f"❌ Erro ao acessar site: {str(e)}")
    
    return None

def handle_start(chat_id: str):
    """Responde ao comando /start"""
    mensagem = """
🚇 *Bem-vindo ao Monitor Linhas SP!*

Eu sou um bot que monitora o status das linhas do Metrô/CPTM de São Paulo em tempo real.

📋 *COMANDOS DISPONÍVEIS:*

/start - Exibir esta mensagem
/linha [número] - Verificar status de uma linha específica
  Exemplo: `/linha 2` (Linha 2-Verde)
  Exemplo: `/linha 15` (Linha 15-Prata)

/todos - Verificar status de TODAS as linhas

🔢 *NÚMEROS DAS LINHAS:*
• 1 - Azul (Metrô)
• 2 - Verde (Metrô)
• 3 - Vermelha (Metrô)
• 4 - Amarela (ViaQuatro)
• 5 - Lilás (ViaMobilidade)
• 7 - Rubi (CPTM)
• 8 - Diamante (ViaMobilidade)
• 9 - Esmeralda (ViaMobilidade)
• 10 - Turquesa (CPTM)
• 11 - Coral (CPTM)
• 12 - Safira (CPTM)
• 13 - Jade (CPTM)
• 15 - Prata (Metrô)

🤖 *NOTIFICAÇÕES AUTOMÁTICAS:*
Além dos comandos, você receberá atualizações automáticas todos os dias às 7h, 17h e 22h.

Digite `/todos` para ver o status agora mesmo!
"""
    send_telegram_message(chat_id, mensagem)

def handle_linha(chat_id: str, linha_id: str):
    """Responde ao comando /linha [número]"""
    # Remove espaços e verifica se é número
    linha_id = linha_id.strip()
    
    if not linha_id.isdigit():
        send_telegram_message(chat_id, "❌ *Formato inválido!*\n\nUse: `/linha [número]`\nExemplo: `/linha 2`")
        return
    
    resultado = verificar_linha_especifica(linha_id)
    
    if resultado is None:
        linhas_disponiveis = ", ".join(sorted(TODAS_LINHAS.keys()))
        mensagem = f"❌ *Linha não encontrada!*\n\nLinhas disponíveis: {linhas_disponiveis}\n\nExemplo: `/linha 2`"
        send_telegram_message(chat_id, mensagem)
        return
    
    now = get_sp_time()
    mensagem = f"🚇 *Status da {resultado['nome']}*\n\n"
    mensagem += f"📊 *Status:* {resultado['status']}\n"
    if resultado['detalhes']:
        mensagem += f"ℹ️ *Detalhes:* {resultado['detalhes']}\n"
    mensagem += f"🏢 *Operadora:* {resultado['operadora']}\n"
    mensagem += f"🕐 *Consultado:* {now}\n\n"
    mensagem += f"Digite `/todos` para ver todas as linhas."
    
    send_telegram_message(chat_id, mensagem)

def handle_todos(chat_id: str):
    """Responde ao comando /todos"""
    send_telegram_message(chat_id, "🔍 Consultando todas as linhas... Isso pode levar alguns segundos.")
    
    resultados = verificar_todas_linhas()
    
    if not resultados:
        send_telegram_message(chat_id, "❌ *Erro ao consultar linhas!*\nO site pode estar fora do ar temporariamente.")
        return
    
    now = get_sp_time()
    mensagem = f"🚇 *Status de TODAS as Linhas - {now}*\n\n"
    
    # Agrupa por operadora
    linhas_por_operadora = {}
    for r in resultados:
        operadora = r['operadora']
        if operadora not in linhas_por_operadora:
            linhas_por_operadora[operadora] = []
        linhas_por_operadora[operadora].append(r)
    
    for operadora, linhas in linhas_por_operadora.items():
        mensagem += f"*{operadora}:*\n"
        for linha in linhas:
            mensagem += f"  • *Linha {linha['id']}* - {linha['nome']}: {linha['status']}"
            if linha['detalhes']:
                mensagem += f" _{linha['detalhes']}_"
            mensagem += "\n"
        mensagem += "\n"
    
    mensagem += "---\n"
    mensagem += f"🕐 Atualizado: {now}\n"
    mensagem += "Digite `/linha [número]` para ver uma linha específica."
    
    send_telegram_message(chat_id, mensagem)

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    """Recebe atualizações do Telegram via webhook"""
    update = request.get_json()
    
    if 'message' in update and 'text' in update['message']:
        chat_id = str(update['message']['chat']['id'])
        text = update['message']['text'].strip()
        
        print(f"📩 Mensagem recebida de {chat_id}: {text}")
        
        if text == '/start':
            handle_start(chat_id)
        elif text == '/todos':
            handle_todos(chat_id)
        elif text.startswith('/linha'):
            partes = text.split(' ', 1)
            if len(partes) > 1:
                linha_id = partes[1].strip()
                handle_linha(chat_id, linha_id)
            else:
                send_telegram_message(chat_id, "❌ *Use:* `/linha [número]`\nExemplo: `/linha 2`")
        else:
            send_telegram_message(chat_id, "❌ *Comando não reconhecido!*\n\nDigite `/start` para ver os comandos disponíveis.")
    
    return 'OK', 200

@app.route('/')
def index():
    return 'Bot está rodando!', 200

def enviar_notificacao_automatica():
    """Função para enviar notificações automáticas agendadas"""
    if not CHAT_ID:
        print("❌ CHAT_ID não configurado para notificações automáticas")
        return
    
    print(f"🚇 Enviando notificação automática - {get_sp_time()}")
    
    resultados = verificar_todas_linhas()
    
    if not resultados:
        send_telegram_message(CHAT_ID, "❌ *Erro na verificação automática!*\nO site pode estar fora do ar.")
        return
    
    now = get_sp_time()
    mensagem = f"🚇 *Status Automático das Linhas - {now}*\n\n"
    
    # Mostra apenas as linhas com problemas primeiro (se houver)
    linhas_com_problema = [r for r in resultados if "✅" not in r['status']]
    linhas_normais = [r for r in resultados if "✅" in r['status']]
    
    if linhas_com_problema:
        mensagem += "⚠️ *LINHAS COM PROBLEMAS:*\n"
        for linha in linhas_com_problema:
            mensagem += f"  • *Linha {linha['id']}*: {linha['status']}\n"
        mensagem += "\n"
    
    if linhas_normais and not ALERTAR_FALHA:
        mensagem += "✅ *LINHAS NORMAIS:*\n"
        for linha in linhas_normais[:5]:  # Mostra só as primeiras 5 para não poluir
            mensagem += f"  • *Linha {linha['id']}*: OK\n"
        if len(linhas_normais) > 5:
            mensagem += f"  ... e mais {len(linhas_normais)-5} linhas normais\n"
        mensagem += "\n"
    
    mensagem += "---\n"
    mensagem += f"🕐 Atualizado: {now}\n"
    mensagem += "Digite `/todos` para ver todas as linhas."
    
    # Decide se envia baseado na configuração
    if ALERTAR_FALHA and not linhas_com_problema:
        print("✅ Tudo normal - Alerta automático suprimido (configurado para só alertar falhas)")
        return
    
    send_telegram_message(CHAT_ID, mensagem)

def setup_webhook():
    """Configura o webhook no Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    # Substitua pela URL do seu serviço (ngrok, Render, etc)
    webhook_url = os.environ.get('WEBHOOK_URL', '')
    
    if webhook_url:
        response = requests.post(url, json={'url': f'{webhook_url}/{TELEGRAM_TOKEN}'})
        if response.status_code == 200:
            print("✅ Webhook configurado com sucesso!")
        else:
            print(f"❌ Erro ao configurar webhook: {response.text}")

def main():
    """Função principal para notificações automáticas (quando executado via GitHub Actions)"""
    print(f"🚇 Iniciando verificação automática - {get_sp_time()}")
    enviar_notificacao_automatica()

if __name__ == "__main__":
    # Se estiver rodando no GitHub Actions, executa a função principal
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        main()
    else:
        # Se estiver rodando como servidor web, configura o bot interativo
        setup_webhook()
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)

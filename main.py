import os
import json
import requests
from datetime import datetime

# Configurações
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
WEBSITES_JSON = os.environ.get('WEBSITES')

def send_telegram_message(message):
    """Envia mensagem para o Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

def check_website(name, url, validation_text):
    """Verifica se o site contém o texto esperado"""
    try:
        response = requests.get(url, timeout=30)
        if validation_text in response.text:
            return "✅ Operação Normal"
        else:
            return "⚠️ PROBLEMA - Site mudou"
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def main():
    # Carrega a lista de sites
    websites = json.loads(WEBSITES_JSON)
    
    # Data/hora atual
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Monta mensagem
    mensagem = f"🚇 *Status das Linhas - {now}*\n\n"
    
    # Verifica cada site
    for site in websites:
        status = check_website(
            site['name'], 
            site['url'], 
            site['validation_text']
        )
        mensagem += f"{site['name']}: {status}\n"
    
    # Envia para o Telegram
    send_telegram_message(mensagem)
    print("Mensagem enviada com sucesso!")

if __name__ == "__main__":
    main()

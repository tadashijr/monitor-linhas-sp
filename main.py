import os
import json
import requests
from datetime import datetime
import pytz
from typing import Dict, List, Any
import time

# Configurações
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
WEBSITES_JSON = os.environ.get('WEBSITES')

# Timeout para requisições
TIMEOUT = 30
# Forçar notificação mesmo sem mudança?
ALWAYS_NOTIFY = True  # Mude para False se quiser apenas quando houver problema

# Arquivo para cache de status (opcional - para detectar mudanças)
STATUS_CACHE_FILE = 'status_cache.json'

def get_sp_time() -> str:
    """Retorna a data/hora atual no fuso de São Paulo"""
    fuso_sp = pytz.timezone('America/Sao_Paulo')
    agora_utc = datetime.now(pytz.UTC)
    agora_sp = agora_utc.astimezone(fuso_sp)
    return agora_sp.strftime("%d/%m/%Y %H:%M:%S")

def send_telegram_message(message: str) -> bool:
    """
    Envia mensagem para o Telegram
    Retorna True se sucesso, False caso contrário
    """
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Erro: TELEGRAM_TOKEN ou CHAT_ID não configurados")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Telegram tem limite de 4096 caracteres
    if len(message) > 4000:
        message = message[:4000] + "...\n\n(mensagem truncada)"
    
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, data=data, timeout=15)
        if response.status_code == 200:
            print("✅ Mensagem enviada com sucesso para o Telegram")
            return True
        else:
            print(f"❌ Erro na API do Telegram: {response.status_code}")
            print(f"Resposta: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Timeout ao enviar mensagem para o Telegram")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado ao enviar mensagem: {str(e)}")
        return False

def check_website(name: str, url: str, validation_text: str, validation_type: str = 'text') -> Dict[str, Any]:
    """
    Verifica se o site contém o texto esperado
    Retorna dicionário com status e detalhes
    """
    resultado = {
        'name': name,
        'url': url,
        'success': False,
        'status': '❌ Erro',
        'details': '',
        'response_time': 0
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=TIMEOUT, headers=headers)
        response_time = round(time.time() - start_time, 2)
        
        resultado['response_time'] = response_time
        
        if response.status_code == 200:
            if validation_type == 'text':
                if validation_text in response.text:
                    resultado['success'] = True
                    resultado['status'] = '✅ Operação Normal'
                    resultado['details'] = f'Tempo: {response_time}s'
                else:
                    resultado['status'] = '⚠️ ALERTA - Texto não encontrado'
                    resultado['details'] = f'Texto "{validation_text}" não encontrado'
            
            elif validation_type == 'status_code':
                resultado['success'] = True
                resultado['status'] = '✅ OK'
                resultado['details'] = f'Status: {response.status_code}'
        else:
            resultado['status'] = f'❌ HTTP {response.status_code}'
            resultado['details'] = f'Erro HTTP: {response.status_code}'
            
    except requests.exceptions.Timeout:
        resultado['status'] = '❌ Timeout'
        resultado['details'] = f'Site não respondeu em {TIMEOUT}s'
    except requests.exceptions.ConnectionError:
        resultado['status'] = '❌ Erro de conexão'
        resultado['details'] = 'Não foi possível conectar ao site'
    except Exception as e:
        resultado['status'] = '❌ Exceção'
        resultado['details'] = str(e)[:100]
    
    return resultado

def load_previous_status() -> Dict[str, str]:
    """Carrega status anterior do cache"""
    try:
        if os.path.exists(STATUS_CACHE_FILE):
            with open(STATUS_CACHE_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_current_status(status: Dict[str, str]):
    """Salva status atual no cache"""
    try:
        with open(STATUS_CACHE_FILE, 'w') as f:
            json.dump(status, f)
    except:
        pass

def should_notify(current: Dict, previous: Dict) -> bool:
    """Decide se deve notificar baseado nas mudanças"""
    if ALWAYS_NOTIFY:
        return True
    
    # Verifica se houve mudança no status
    for site in current['results']:
        site_name = site['name']
        current_status = site['status']
        previous_status = previous.get(site_name, '')
        
        if current_status != previous_status:
            return True
    
    return False

def main():
    """Função principal"""
    print(f"🚇 Iniciando verificação - {get_sp_time()}")
    
    # Verifica configurações básicas
    if not TELEGRAM_TOKEN:
        print("❌ ERRO: TELEGRAM_TOKEN não configurado")
        return
    
    if not CHAT_ID:
        print("❌ ERRO: CHAT_ID não configurado")
        return
    
    if not WEBSITES_JSON:
        print("❌ ERRO: WEBSITES não configurado")
        return
    
    try:
        # Carrega lista de sites
        websites = json.loads(WEBSITES_JSON)
        print(f"📋 Monitorando {len(websites)} linhas")
        
        # Carrega status anterior
        previous_status = load_previous_status()
        
        # Prepara resultado
        now = get_sp_time()
        mensagem = f"🚇 *Status das Linhas - {now}*\n\n"
        
        # Verifica cada site
        results = []
        novos_status = {}
        
        for i, site in enumerate(websites, 1):
            print(f"🔄 Verificando {i}/{len(websites)}: {site['name']}")
            
            resultado = check_website(
                site['name'],
                site['url'],
                site.get('validation_text', 'Operação Normal'),
                site.get('validation_type', 'text')
            )
            
            results.append(resultado)
            novos_status[site['name']] = resultado['status']
            
            # Adiciona à mensagem
            mensagem += f"*{resultado['name']}:*\n"
            mensagem += f"{resultado['status']}"
            if resultado['details']:
                mensagem += f" _{resultado['details']}_"
            mensagem += "\n\n"
        
        # Adiciona rodapé
        mensagem += "---\n"
        mensagem += f"🕐 Atualizado: {now}\n"
        mensagem += f"🔍 Verificação automática via GitHub Actions"
        
        # Decide se envia notificação
        current_data = {'results': results, 'timestamp': now}
        
        if should_notify(current_data, previous_status):
            print("📤 Mudança detectada ou notificação forçada - Enviando alerta...")
            send_telegram_message(mensagem)
            # Salva novo status
            save_current_status(novos_status)
        else:
            print("📊 Status inalterado - Nenhuma notificação enviada")
        
        print(f"✅ Verificação concluída com sucesso!")
        
    except json.JSONDecodeError as e:
        erro_msg = f"❌ Erro ao decodificar WEBSITES JSON: {str(e)}"
        print(erro_msg)
        send_telegram_message(f"🚨 *ERRO DE CONFIGURAÇÃO*\n\n{erro_msg}")
    
    except Exception as e:
        erro_msg = f"❌ Erro inesperado: {str(e)}"
        print(erro_msg)
        send_telegram_message(f"🚨 *ERRO NO BOT*\n\n{erro_msg}")

if __name__ == "__main__":
    main()

import os
import json
import requests
from datetime import datetime
import pytz
from typing import Dict, List, Any, Optional
import time

# Configurações
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
WEBSITES_JSON = os.environ.get('WEBSITES')
ALERTAR_FALHA = os.environ.get('ALERTAR_FALHA', 'false').lower() == 'true'

# Timeout para requisições
TIMEOUT = 30
# Arquivo para cache de status
STATUS_CACHE_FILE = 'status_cache.json'

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

def get_sp_time() -> str:
    """Retorna a data/hora atual no fuso de São Paulo"""
    fuso_sp = pytz.timezone('America/Sao_Paulo')
    agora_utc = datetime.now(pytz.UTC)
    agora_sp = agora_utc.astimezone(fuso_sp)
    return agora_sp.strftime("%d/%m/%Y %H:%M:%S")

def send_telegram_message(message: str) -> bool:
    """Envia mensagem para o Telegram"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Erro: TELEGRAM_TOKEN ou CHAT_ID não configurados")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
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
            return False
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {str(e)}")
        return False

def extrair_status_linha(html_content: str, nome_linha: str) -> Dict[str, Any]:
    """
    Extrai o status de uma linha específica do HTML
    """
    resultado = {
        'status': '❓ Não encontrado',
        'detalhes': '',
        'success': False
    }
    
    try:
        # Procura pela linha no HTML
        if nome_linha in html_content:
            # Pega o contexto ao redor da linha (500 caracteres depois)
            index = html_content.find(nome_linha)
            contexto = html_content[index:index + 500]
            
            # Procura por padrões de status
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

def verificar_todas_linhas(url: str) -> List[Dict[str, Any]]:
    """
    Verifica todas as linhas disponíveis no site
    """
    resultados = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, timeout=TIMEOUT, headers=headers)
        
        if response.status_code == 200:
            html = response.text
            
            # Verifica cada linha
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
        else:
            print(f"❌ Erro HTTP ao acessar site: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao acessar site: {str(e)}")
    
    return resultados

def verificar_linhas_selecionadas(linhas_escolhidas: List[str], url: str) -> List[Dict[str, Any]]:
    """
    Verifica apenas as linhas selecionadas pelo usuário
    """
    resultados = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, timeout=TIMEOUT, headers=headers)
        
        if response.status_code == 200:
            html = response.text
            
            for linha_id in linhas_escolhidas:
                if linha_id in TODAS_LINHAS:
                    linha_info = TODAS_LINHAS[linha_id]
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

def verificar_falhas(resultados: List[Dict]) -> bool:
    """
    Verifica se há alguma falha nas linhas monitoradas
    """
    for resultado in resultados:
        if "✅" not in resultado['status'] and "Operação Normal" not in resultado['status']:
            return True
    return False

def main():
    """Função principal"""
    print(f"🚇 Iniciando verificação - {get_sp_time()}")
    
    # URL do site
    URL = "https://ccm.artesp.sp.gov.br/metroferroviario/status-linhas/"
    
    # Carrega configuração das linhas a monitorar
    linhas_monitorar = []
    monitorar_todas = False
    
    if WEBSITES_JSON:
        try:
            config = json.loads(WEBSITES_JSON)
            if isinstance(config, list):
                for item in config:
                    if 'id' in item:
                        linhas_monitorar.append(item['id'])
                    elif 'name' in item and "todas" in item['name'].lower():
                        monitorar_todas = True
        except:
            # Se não conseguir parsear, usa configuração padrão
            linhas_monitorar = ['2', '15']
    else:
        # Configuração padrão: linhas 2 e 15
        linhas_monitorar = ['2', '15']
    
    print(f"📋 Monitorando: {', '.join(linhas_monitorar) if linhas_monitorar else 'TODAS as linhas'}")
    
    # Verifica as linhas
    if monitorar_todas:
        resultados = verificar_todas_linhas(URL)
    else:
        resultados = verificar_linhas_selecionadas(linhas_monitorar, URL)
    
    if not resultados:
        print("❌ Nenhum resultado obtido")
        send_telegram_message("🚨 *ERRO*\n\nNão foi possível obter o status das linhas. O site pode estar fora do ar.")
        return
    
    # Monta mensagem
    now = get_sp_time()
    mensagem = f"🚇 *Status das Linhas - {now}*\n\n"
    
    # Agrupa por operadora
    linhas_por_operadora = {}
    for r in resultados:
        operadora = r['operadora']
        if operadora not in linhas_por_operadora:
            linhas_por_operadora[operadora] = []
        linhas_por_operadora[operadora].append(r)
    
    # Monta mensagem organizada
    for operadora, linhas in linhas_por_operadora.items():
        mensagem += f"*{operadora}:*\n"
        for linha in linhas:
            mensagem += f"  • {linha['nome']}: {linha['status']}"
            if linha['detalhes']:
                mensagem += f" _{linha['detalhes']}_"
            mensagem += "\n"
        mensagem += "\n"
    
    mensagem += "---\n"
    mensagem += f"🕐 Atualizado: {now}\n"
    
    # Verifica se há falhas
    tem_falha = verificar_falhas(resultados)
    
    # Decide se envia alerta
    if tem_falha and ALERTAR_FALHA:
        mensagem = "🚨 *ALERTA DE FALHA DETECTADA*\n\n" + mensagem
        send_telegram_message(mensagem)
        print("⚠️ Falha detectada - Alerta enviado!")
    
    elif not tem_falha and ALERTAR_FALHA:
        # Se configurado para alertar só em falha, não envia
        print("✅ Tudo normal - Nenhum alerta enviado (configurado para só alertar em falhas)")
    
    else:
        # Envia relatório normal
        send_telegram_message(mensagem)
        print("📊 Relatório normal enviado")

if __name__ == "__main__":
    main()

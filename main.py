import os
import json
import requests
from datetime import datetime
import pytz
from typing import Dict, List, Any, Optional
from flask import Flask, request
import time

# ============================================
# CONFIGURAÇÕES
# ============================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
WEBSITES_JSON = os.environ.get('WEBSITES')
ALERTAR_FALHA = os.environ.get('ALERTAR_FALHA', 'false').lower() == 'true'
HG_WEATHER_TOKEN = os.environ.get('HG_WEATHER_TOKEN')
PORT = int(os.environ.get('PORT', 10000))
SITE_URL = "https://ccm.artesp.sp.gov.br/metroferroviario/status-linhas/"
TIMEOUT = 30

# ============================================
# TODAS AS LINHAS DISPONÍVEIS
# ============================================
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

# ============================================
# MAPA DE LINHAS POR REGIÃO (PARA O CLIMA)
# ============================================
LINHAS_POR_REGIAO = {
    "1": {
        "nome": "Linha 1-Azul",
        "regioes": ["Norte", "Centro", "Sul"],
        "bairros": ["Tucuruvi", "Santana", "Sé", "Jabaquara"],
        "temp_media_metro": 20,
        "estacoes_chave": ["Tucuruvi", "Santana", "Sé", "Jabaquara"]
    },
    "2": {
        "nome": "Linha 2-Verde",
        "regioes": ["Vila Prudente", "Centro", "Alto de Pinheiros"],
        "bairros": ["Vila Prudente", "Paraíso", "Consolação", "Clínicas", "Alto de Pinheiros"],
        "temp_media_metro": 21,
        "estacoes_chave": ["Vila Prudente", "Paraíso", "Consolação", "Clínicas", "Alto de Pinheiros"]
    },
    "3": {
        "nome": "Linha 3-Vermelha",
        "regioes": ["Leste", "Centro", "Barra Funda"],
        "bairros": ["Corinthians-Itaquera", "Tatuapé", "Sé", "Barra Funda"],
        "temp_media_metro": 19,
        "estacoes_chave": ["Corinthians-Itaquera", "Tatuapé", "Sé", "Barra Funda"]
    },
    "4": {
        "nome": "Linha 4-Amarela",
        "regioes": ["Luz", "Paulista", "Morumbi"],
        "bairros": ["Luz", "República", "Paulista", "Faria Lima", "Morumbi"],
        "temp_media_metro": 20,
        "arborizada": True,
        "estacoes_arvores": ["Trianon-Masp", "Clínicas"],
        "estacoes_chave": ["Luz", "República", "Paulista", "Faria Lima", "Morumbi"]
    },
    "5": {
        "nome": "Linha 5-Lilás",
        "regioes": ["Sul", "Santo Amaro"],
        "bairros": ["Capão Redondo", "Santo Amaro", "Chácara Klabin"],
        "temp_media_metro": 22,
        "estacoes_chave": ["Capão Redondo", "Santo Amaro", "Chácara Klabin"]
    },
    "7": {
        "nome": "Linha 7-Rubi",
        "regioes": ["Noroeste", "Franco da Rocha"],
        "bairros": ["Luz", "Pirituba", "Franco da Rocha", "Jundiaí"],
        "temp_media_metro": 19,
        "trem_ar_condicionado": True,
        "estacoes_chave": ["Luz", "Pirituba", "Franco da Rocha", "Jundiaí"]
    },
    "8": {
        "nome": "Linha 8-Diamante",
        "regioes": ["Oeste", "Barueri"],
        "bairros": ["Júlio Prestes", "Osasco", "Barueri", "Itapevi"],
        "temp_media_metro": 21,
        "estacoes_chave": ["Júlio Prestes", "Osasco", "Barueri", "Itapevi"]
    },
    "9": {
        "nome": "Linha 9-Esmeralda",
        "regioes": ["Sudoeste", "Granja Viana"],
        "bairros": ["Osasco", "Pinheiros", "Santo Amaro", "Granja Viana"],
        "temp_media_metro": 20,
        "estacoes_chave": ["Osasco", "Pinheiros", "Santo Amaro", "Granja Viana"]
    },
    "10": {
        "nome": "Linha 10-Turquesa",
        "regioes": ["Sudeste", "ABC"],
        "bairros": ["Brás", "São Caetano", "Santo André", "Mauá", "Rio Grande da Serra"],
        "temp_media_metro": 22,
        "estacoes_chave": ["Brás", "São Caetano", "Santo André", "Mauá"]
    },
    "11": {
        "nome": "Linha 11-Coral",
        "regioes": ["Leste", "Mogi"],
        "bairros": ["Luz", "Tatuapé", "Itaquera", "Mogi das Cruzes"],
        "temp_media_metro": 21,
        "estacoes_chave": ["Luz", "Tatuapé", "Itaquera", "Mogi das Cruzes"]
    },
    "12": {
        "nome": "Linha 12-Safira",
        "regioes": ["Leste", "Itaim Paulista"],
        "bairros": ["Brás", "Tatuapé", "Itaim Paulista"],
        "temp_media_metro": 21,
        "estacoes_chave": ["Brás", "Tatuapé", "Itaim Paulista"]
    },
    "13": {
        "nome": "Linha 13-Jade",
        "regioes": ["Aeroporto Guarulhos"],
        "bairros": ["Engenheiro Goulart", "Aeroporto Guarulhos"],
        "temp_media_metro": 20,
        "estacoes_chave": ["Engenheiro Goulart", "Aeroporto Guarulhos"]
    },
    "15": {
        "nome": "Linha 15-Prata",
        "regioes": ["Leste", "São Mateus"],
        "bairros": ["Vila Prudente", "São Mateus", "Cidade Tiradentes"],
        "temp_media_metro": 23,
        "elevado": True,
        "estacoes_chave": ["Vila Prudente", "São Mateus", "Cidade Tiradentes"]
    }
}

app = Flask(__name__)

# ============================================
# FUNÇÕES AUXILIARES
# ============================================
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

# ============================================
# FUNÇÕES DO METRÔ
# ============================================
def extrair_status_linha(html_content: str, nome_linha: str) -> Dict[str, Any]:
    """Extrai o status de uma linha específica do HTML"""
    resultado = {
        'status': '❓ Não encontrado',
        'detalhes': '',
        'success': False
    }
    
    try:
        # Lista de possíveis variações do nome da linha
        variacoes_nome = [
            nome_linha,
            nome_linha.replace("-", " "),
            nome_linha.replace("-", " - "),
            nome_linha.split("-")[0].strip(),
        ]
        
        # Para linha 4, adiciona variações específicas
        if "4" in nome_linha:
            variacoes_nome.extend([
                "ViaQuatro",
                "Linha 4",
                "Amarela"
            ])
        
        # Procura por qualquer variação
        encontrado = False
        contexto = ""
        
        for variacao in variacoes_nome:
            if variacao in html_content:
                index = html_content.find(variacao)
                contexto = html_content[index:index + 800]
                encontrado = True
                print(f"✅ Encontrou variação: '{variacao}'")
                break
        
        if encontrado:
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
                resultado['detalhes'] = "Linha encontrada mas status não identificado"
        else:
            print(f"❌ Linha '{nome_linha}' não encontrada no HTML")
            
    except Exception as e:
        resultado['detalhes'] = str(e)[:50]
        print(f"❌ Erro na extração: {str(e)}")
    
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

# ============================================
# CLASSE: HG WEATHER API (100% GRATUITA)
# ============================================
class HGWeatherAPI:
    """Integração com a API gratuita da HG Brasil"""
    
    def __init__(self):
        self.token = HG_WEATHER_TOKEN
        self.base_url = "https://api.hgbrasil.com/weather"
        self.cache = {}
        self.cache_expiration = 1800  # 30 minutos
    
    def get_previsao(self, linha_id):
        """Busca previsão do tempo para a região da linha"""
        if not self.token:
            print("⚠️ Token da HG Weather não configurado")
            return None
            
        if linha_id not in LINHAS_POR_REGIAO:
            return None
        
        # Pega o primeiro bairro como referência
        bairros = LINHAS_POR_REGIAO[linha_id].get('bairros', ['São Paulo'])
        cidade_ref = bairros[0]
        
        # Verifica cache
        cache_key = f"weather_{linha_id}"
        if cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if time.time() - cache_time < self.cache_expiration:
                return cache_data
        
        try:
            # Parâmetros da requisição
            params = {
                'key': self.token,
                'city_name': f"{cidade_ref},SP",
                'format': 'json-cors'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verifica se a requisição foi bem-sucedida
                if data.get('valid_key', False) and data.get('results'):
                    self.cache[cache_key] = (time.time(), data)
                    return data
                else:
                    print(f"❌ Erro na API HG: {data.get('message', 'Erro desconhecido')}")
                    return None
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao buscar clima: {str(e)}")
            return None
    
    def recomendar_guarda_chuva(self, linha_id):
        """Recomenda guarda-chuva baseado na previsão"""
        dados = self.get_previsao(linha_id)
        
        if not dados or 'results' not in dados:
            return "❓ Não foi possível verificar chuva", "🤷"
        
        results = dados['results']
        
        # Dados de chuva
        chuva_mm = results.get('rain', 0)
        
        # Pega previsão do dia atual no forecast
        forecast = results.get('forecast', [])
        hoje = forecast[0] if forecast else {}
        prob_chuva = hoje.get('rain_probability', 0)
        
        # Se não veio no rain, pega do forecast
        if chuva_mm == 0 and 'rain' in hoje:
            chuva_mm = hoje.get('rain', 0)
        
        # Ajuste para linhas elevadas (ex: 15-Prata)
        if linha_id == "15" or LINHAS_POR_REGIAO.get(linha_id, {}).get('elevado', False):
            chuva_mm *= 1.5
        
        if chuva_mm >= 5 or prob_chuva > 70:
            return f"🌧️ **LEVA GUARDA-CHUVA!** Probabilidade {prob_chuva}% de chuva ({chuva_mm:.1f}mm)", "☔"
        elif chuva_mm >= 1 or prob_chuva > 30:
            return f"🌦️ **Melhor levar**... Pode garoar ({chuva_mm:.1f}mm, {prob_chuva}%)", "☂️"
        else:
            return "☀️ **Pode deixar em casa**! Sem chuva prevista", "😎"
    
    def recomendar_blusa(self, linha_id):
        """Recomenda blusa baseado na temperatura"""
        dados = self.get_previsao(linha_id)
        
        if not dados or 'results' not in dados:
            return "❓ Temperatura não disponível", "🤷"
        
        results = dados['results']
        
        temp_atual = results.get('temp', 22)
        descricao = results.get('description', '')
        umidade = results.get('humidity', 0)
        
        # Temperatura interna do metrô
        temp_metro = LINHAS_POR_REGIAO.get(linha_id, {}).get('temp_media_metro', 21)
        diferenca = abs(temp_atual - temp_metro)
        
        if temp_atual <= 15:
            msg = f"🥶 **CASACÃO PESADO!** Tá frio: {temp_atual}°C"
            emoji = "🧥❄️"
        elif temp_atual <= 18:
            msg = f"🧥 **Leva blusa de frio** ({temp_atual}°C)"
            emoji = "🧥"
        elif temp_atual <= 22:
            msg = f"👕 **Blusa leve** ({temp_atual}°C - {descricao})"
            emoji = "👕"
        elif temp_atual <= 28:
            msg = f"😎 **Roupa leve** ({temp_atual}°C)"
            emoji = "🩳"
        else:
            msg = f"🔥 **Calorão!** {temp_atual}°C - roupa bem fresca"
            emoji = "🩴"
        
        if diferenca > 5:
            msg += f"\n⚠️ Diferença de {diferenca}° com o metrô - leve uma blusa extra!"
        
        # Informação extra de umidade
        if umidade > 80:
            msg += f"\n💧 Umidade alta ({umidade}%) - sensação de frio maior"
        elif umidade < 30:
            msg += f"\n☀️ Umidade baixa ({umidade}%) - hidrate-se!"
        
        # Dica extra para linhas arborizadas
        if LINHAS_POR_REGIAO.get(linha_id, {}).get('arborizada', False):
            msg += f"\n🌳 Estação Trianon tem clima mais ameno pelo parque!"
        
        return msg, emoji
    
    def gerar_recomendacao_por_linha(self, linha_id):
        """Gera recomendação completa usando HG Weather API"""
        if linha_id not in LINHAS_POR_REGIAO:
            return None
        
        msg_chuva, emoji_chuva = self.recomendar_guarda_chuva(linha_id)
        msg_blusa, emoji_blusa = self.recomendar_blusa(linha_id)
        
        dados = self.get_previsao(linha_id)
        
        if dados and 'results' in dados:
            results = dados['results']
            cidade = results.get('city', 'São Paulo')
            temp = results.get('temp', '?')
            desc = results.get('description', '')
            umidade = results.get('humidity', '?')
            vento = results.get('wind_speedy', '?')
            
            # Pega previsão de hoje
            forecast = results.get('forecast', [])
            hoje = forecast[0] if forecast else {}
            max_temp = hoje.get('max', '?')
            min_temp = hoje.get('min', '?')
        else:
            cidade = "São Paulo"
            temp = "?"
            desc = ""
            umidade = "?"
            vento = "?"
            max_temp = "?"
            min_temp = "?"
        
        mensagem = f"""
🚇 *Recomendação para {LINHAS_POR_REGIAO[linha_id]['nome']}*

📍 *Região:* {cidade}
🌡️ *Agora:* {temp}°C - {desc}
📊 *Máx/Mín:* {max_temp}° / {min_temp}°
💧 *Umidade:* {umidade}% | 🌬️ *Vento:* {vento}

🌤️ *Recomendações:*
{msg_chuva}
{msg_blusa}

---
💡 *Linha:* {LINHAS_POR_REGIAO[linha_id]['nome']}
🕐 *Atualizado:* {get_sp_time()}
⚡ Dados via HG Weather (gratuito)
"""
        return mensagem
    
    def gerar_previsao_5dias(self, linha_id):
        """Gera previsão resumida para 5 dias"""
        if linha_id not in LINHAS_POR_REGIAO:
            return None
        
        dados = self.get_previsao(linha_id)
        
        if not dados or 'results' not in dados:
            return "❌ Não foi possível buscar previsão"
        
        results = dados['results']
        cidade = results.get('city', 'São Paulo')
        forecast = results.get('forecast', [])
        
        if not forecast:
            return "❌ Previsão não disponível"
        
        msg = f"📅 *Previsão 5 dias - {cidade}*\n\n"
        
        for i, dia in enumerate(forecast[:5]):
            data = dia.get('date', '')
            if data:
                # Formata data de YYYY-MM-DD para DD/MM
                partes = data.split('-')
                if len(partes) == 3:
                    data_formatada = f"{partes[2]}/{partes[1]}"
                else:
                    data_formatada = data
            
            semana = dia.get('weekday', '')
            max_temp = dia.get('max', '?')
            min_temp = dia.get('min', '?')
            chuva = dia.get('rain', 0)
            prob = dia.get('rain_probability', 0)
            desc = dia.get('description', '')
            
            msg += f"*{data_formatada} ({semana})*\n"
            msg += f"🌡️ {min_temp}° ~ {max_temp}° | 🌧️ {chuva}mm ({prob}%)\n"
            msg += f"📝 {desc}\n\n"
        
        return msg

# ============================================
# FUNÇÕES DOS ALERTAS
# ============================================
def enviar_alerta_linhas():
    """Envia alerta das linhas 2, 4 e 15 + clima"""
    if not CHAT_ID:
        print("❌ CHAT_ID não configurado para alertas")
        return
    
    # Verifica se é dia útil (segunda a sexta)
    agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
    dia_semana = agora.weekday()
    
    if dia_semana >= 5:
        print(f"📅 Final de semana - Alerta suprimido")
        return
    
    print(f"🚇 Enviando alerta das linhas 2,4,15 - {get_sp_time()}")
    
    # Linhas para alertar
    linhas_alertar = ["2", "4", "15"]
    
    resultados = verificar_todas_linhas()
    
    if not resultados:
        send_telegram_message(CHAT_ID, "❌ *Erro na verificação das linhas!*\nO site pode estar fora do ar.")
        return
    
    now = get_sp_time()
    mensagem = f"🚇 *Alerta Diário - {now}*\n\n"
    
    # Status das linhas
    for linha_id in linhas_alertar:
        for resultado in resultados:
            if resultado['id'] == linha_id:
                mensagem += f"*{resultado['nome']}:* {resultado['status']}\n"
                if resultado['detalhes']:
                    mensagem += f"  _{resultado['detalhes']}_\n"
                break
    
    mensagem += "\n" + "="*30 + "\n\n"
    mensagem += "🌤️ *Clima Personalizado por Linha:*\n\n"
    
    # Clima para cada linha
    clima = HGWeatherAPI()
    for linha_id in linhas_alertar:
        if HG_WEATHER_TOKEN:
            rec = clima.gerar_recomendacao_por_linha(linha_id)
            if rec:
                # Extrai só a parte das recomendações
                partes = rec.split("---")
                linhas_rec = partes[0].split("\n")
                # Pega só as linhas relevantes
                for line in linhas_rec:
                    if "🌧️" in line or "🌦️" in line or "☀️" in line or \
                       "🥶" in line or "🧥" in line or "👕" in line or "😎" in line or "🔥" in line:
                        mensagem += f"*Linha {linha_id}:* {line.strip()}\n"
        else:
            mensagem += f"*Linha {linha_id}:* ⚠️ Token do clima não configurado\n"
    
    mensagem += "\n---\n"
    mensagem += "📊 Para ver todas as linhas, use /todas\n"
    mensagem += "🌤️ Para clima detalhado, use /clima [linha]"
    
    send_telegram_message(CHAT_ID, mensagem)
    print("✅ Alerta enviado com sucesso!")

def executar_modo_github_actions():
    """Função chamada quando executado pelo GitHub Actions"""
    print(f"🚇 Executando no GitHub Actions - {get_sp_time()}")
    
    tipo_alerta = os.environ.get('TIPO_ALERTA', '')
    
    if tipo_alerta == 'linhas_especificas':
        enviar_alerta_linhas()
    else:
        print("ℹ️ Nenhum alerta específico configurado")

def setup_webhook():
    """Configura o webhook no Telegram"""
    render_url = os.environ.get('RENDER_EXTERNAL_URL')
    if render_url and TELEGRAM_TOKEN:
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

# ============================================
# ROTAS DO FLASK (WEBHOOK)
# ============================================
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
🚇 *Bem-vindo ao Monitor Linhas SP + Clima Inteligente!*

📋 *COMANDOS DISPONÍVEIS:*

🚆 *Metrô:*
/linha [número] - Status da linha
/todas - Status de todas as linhas

🌤️ *Clima Inteligente:*
/clima [número] - Recomendação PERSONALIZADA para sua linha
  Ex: `/clima 2` (linha 2-Verde)
  Ex: `/clima 4` (linha 4-Amarela)
  Ex: `/clima 15` (linha 15-Prata)

/previsao [linha] - Previsão de 5 dias para sua região

🤖 *Notificações automáticas:*
Segunda a sexta 7h e 17h: Status linhas 2,4,15 + clima personalizado

🔢 *Linhas disponíveis:* 1,2,3,4,5,7,8,9,10,11,12,13,15
"""
            send_telegram_message(chat_id, mensagem)
            
        elif text == '/todas':
            send_telegram_message(chat_id, "🔍 Consultando...")
            resultados = verificar_todas_linhas()
            
            if resultados:
                now = get_sp_time()
                msg = f"🚇 *Todas as Linhas - {now}*\n\n"
                
                # Agrupa por operadora para melhor visualização
                por_operadora = {}
                for r in resultados:
                    op = r['operadora']
                    if op not in por_operadora:
                        por_operadora[op] = []
                    por_operadora[op].append(r)
                
                for operadora, linhas in por_operadora.items():
                    msg += f"*{operadora}:*\n"
                    for linha in linhas:
                        msg += f"  • *Linha {linha['id']}*: {linha['status']}\n"
                    msg += "\n"
                
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
        
        # ===== COMANDOS DE CLIMA =====
        elif text.startswith('/clima'):
            partes = text.split(' ', 1)
            if len(partes) > 1:
                linha_id = partes[1].strip()
                
                if linha_id in LINHAS_POR_REGIAO:
                    if not HG_WEATHER_TOKEN:
                        send_telegram_message(chat_id, "❌ *Token da HG Weather não configurado!*\n\nEntre em contato com o administrador.")
                        return
                    
                    send_telegram_message(chat_id, "🔍 Consultando clima em tempo real...")
                    
                    clima = HGWeatherAPI()
                    mensagem = clima.gerar_recomendacao_por_linha(linha_id)
                    if mensagem:
                        send_telegram_message(chat_id, mensagem)
                    else:
                        send_telegram_message(chat_id, "❌ Erro ao buscar dados do clima")
                else:
                    msg = f"❌ Linha {linha_id} não encontrada!\nDisponíveis: 1,2,3,4,5,7,8,9,10,11,12,13,15"
                    send_telegram_message(chat_id, msg)
            else:
                msg = """
🌤️ *Recomendação por Linha*

Use: `/clima [número da linha]`

Exemplos:
/clima 2 - Linha 2-Verde
/clima 4 - Linha 4-Amarela
/clima 15 - Linha 15-Prata

🔢 *Linhas disponíveis:* 1,2,3,4,5,7,8,9,10,11,12,13,15
"""
                send_telegram_message(chat_id, msg)
        
        elif text.startswith('/previsao'):
            partes = text.split(' ', 1)
            linha_id = partes[1].strip() if len(partes) > 1 else "2"
            
            if linha_id in LINHAS_POR_REGIAO:
                if not HG_WEATHER_TOKEN:
                    send_telegram_message(chat_id, "❌ *Token da HG Weather não configurado!*")
                    return
                
                send_telegram_message(chat_id, "🔍 Buscando previsão...")
                
                clima = HGWeatherAPI()
                msg = clima.gerar_previsao_5dias(linha_id)
                
                if msg:
                    send_telegram_message(chat_id, msg)
                else:
                    send_telegram_message(chat_id, "❌ Erro ao buscar previsão")
            else:
                send_telegram_message(chat_id, "❌ Linha inválida")
    
    return 'OK', 200

@app.route('/healthz')
def health():
    return 'OK', 200

@app.route('/')
def index():
    return 'Bot Monitor Linhas SP está rodando!', 200

# ============================================
# PONTO DE ENTRADA PRINCIPAL
# ============================================
if __name__ == "__main__":
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        executar_modo_github_actions()
    else:
        print(f"🚇 Bot iniciando em modo servidor - {get_sp_time()}")
        setup_webhook()
        app.run(host='0.0.0.0', port=PORT)

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
        "lat": -23.5505, "lon": -46.6333,  # Centro de SP
        "estacoes_chave": ["Tucuruvi", "Santana", "Sé", "Jabaquara"]
    },
    "2": {
        "nome": "Linha 2-Verde",
        "regioes": ["Vila Prudente", "Centro", "Alto de Pinheiros"],
        "bairros": ["Vila Prudente", "Paraíso", "Consolação", "Clínicas", "Alto de Pinheiros"],
        "temp_media_metro": 21,
        "lat": -23.5717, "lon": -46.6456,  # Paraíso
        "estacoes_chave": ["Vila Prudente", "Paraíso", "Consolação", "Clínicas", "Alto de Pinheiros"]
    },
    "3": {
        "nome": "Linha 3-Vermelha",
        "regioes": ["Leste", "Centro", "Barra Funda"],
        "bairros": ["Corinthians-Itaquera", "Tatuapé", "Sé", "Barra Funda"],
        "temp_media_metro": 19,
        "lat": -23.5337, "lon": -46.5776,  # Tatuapé
        "estacoes_chave": ["Corinthians-Itaquera", "Tatuapé", "Sé", "Barra Funda"]
    },
    "4": {
        "nome": "Linha 4-Amarela",
        "regioes": ["Luz", "Paulista", "Morumbi"],
        "bairros": ["Luz", "República", "Paulista", "Faria Lima", "Morumbi"],
        "temp_media_metro": 20,
        "arborizada": True,
        "lat": -23.5578, "lon": -46.6622,  # Paulista
        "estacoes_arvores": ["Trianon-Masp", "Clínicas"],
        "estacoes_chave": ["Luz", "República", "Paulista", "Faria Lima", "Morumbi"]
    },
    "5": {
        "nome": "Linha 5-Lilás",
        "regioes": ["Sul", "Santo Amaro"],
        "bairros": ["Capão Redondo", "Santo Amaro", "Chácara Klabin"],
        "temp_media_metro": 22,
        "lat": -23.6526, "lon": -46.7073,  # Santo Amaro
        "estacoes_chave": ["Capão Redondo", "Santo Amaro", "Chácara Klabin"]
    },
    "7": {
        "nome": "Linha 7-Rubi",
        "regioes": ["Noroeste", "Franco da Rocha"],
        "bairros": ["Luz", "Pirituba", "Franco da Rocha", "Jundiaí"],
        "temp_media_metro": 19,
        "trem_ar_condicionado": True,
        "lat": -23.5034, "lon": -46.6489,  # Pirituba
        "estacoes_chave": ["Luz", "Pirituba", "Franco da Rocha", "Jundiaí"]
    },
    "8": {
        "nome": "Linha 8-Diamante",
        "regioes": ["Oeste", "Barueri"],
        "bairros": ["Júlio Prestes", "Osasco", "Barueri", "Itapevi"],
        "temp_media_metro": 21,
        "lat": -23.5329, "lon": -46.7917,  # Osasco
        "estacoes_chave": ["Júlio Prestes", "Osasco", "Barueri", "Itapevi"]
    },
    "9": {
        "nome": "Linha 9-Esmeralda",
        "regioes": ["Sudoeste", "Granja Viana"],
        "bairros": ["Osasco", "Pinheiros", "Santo Amaro", "Granja Viana"],
        "temp_media_metro": 20,
        "lat": -23.5673, "lon": -46.6964,  # Pinheiros
        "estacoes_chave": ["Osasco", "Pinheiros", "Santo Amaro", "Granja Viana"]
    },
    "10": {
        "nome": "Linha 10-Turquesa",
        "regioes": ["Sudeste", "ABC"],
        "bairros": ["Brás", "São Caetano", "Santo André", "Mauá", "Rio Grande da Serra"],
        "temp_media_metro": 22,
        "lat": -23.6565, "lon": -46.5285,  # Santo André
        "estacoes_chave": ["Brás", "São Caetano", "Santo André", "Mauá"]
    },
    "11": {
        "nome": "Linha 11-Coral",
        "regioes": ["Leste", "Mogi"],
        "bairros": ["Luz", "Tatuapé", "Itaquera", "Mogi das Cruzes"],
        "temp_media_metro": 21,
        "lat": -23.5629, "lon": -46.3911,  # Itaquera
        "estacoes_chave": ["Luz", "Tatuapé", "Itaquera", "Mogi das Cruzes"]
    },
    "12": {
        "nome": "Linha 12-Safira",
        "regioes": ["Leste", "Itaim Paulista"],
        "bairros": ["Brás", "Tatuapé", "Itaim Paulista"],
        "temp_media_metro": 21,
        "lat": -23.5405, "lon": -46.4161,  # Itaim Paulista
        "estacoes_chave": ["Brás", "Tatuapé", "Itaim Paulista"]
    },
    "13": {
        "nome": "Linha 13-Jade",
        "regioes": ["Aeroporto Guarulhos"],
        "bairros": ["Engenheiro Goulart", "Aeroporto Guarulhos"],
        "temp_media_metro": 20,
        "lat": -23.4356, "lon": -46.4731,  # Aeroporto Guarulhos
        "estacoes_chave": ["Engenheiro Goulart", "Aeroporto Guarulhos"]
    },
    "15": {
        "nome": "Linha 15-Prata",
        "regioes": ["Leste", "São Mateus"],
        "bairros": ["Vila Prudente", "São Mateus", "Cidade Tiradentes"],
        "temp_media_metro": 23,
        "elevado": True,
        "lat": -23.6122, "lon": -46.5633,  # São Mateus
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
# NOVA CLASSE: OPEN-METEO API (100% GRATUITA, SEM TOKEN)
# ============================================
class OpenMeteoAPI:
    """Integração com a API gratuita Open-Meteo (não precisa de token)"""
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.cache = {}
        self.cache_expiration = 1800  # 30 minutos
    
    def get_previsao(self, linha_id):
        """Busca previsão do tempo para a região da linha"""
        if linha_id not in LINHAS_POR_REGIAO:
            return None
        
        # Pega coordenadas da linha
        coord = LINHAS_POR_REGIAO[linha_id]
        lat = coord.get('lat', -23.5505)
        lon = coord.get('lon', -46.6333)
        
        # Verifica cache
        cache_key = f"weather_{linha_id}"
        if cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if time.time() - cache_time < self.cache_expiration:
                return cache_data
        
        try:
            # Parâmetros da requisição
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": ["temperature_2m", "relative_humidity_2m", "weather_code", "wind_speed_10m"],
                "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "precipitation_probability_max", "weather_code"],
                "timezone": "America/Sao_Paulo",
                "forecast_days": 5
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.cache[cache_key] = (time.time(), data)
                return data
            else:
                print(f"❌ Erro Open-Meteo: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao buscar clima: {str(e)}")
            return None
    
    def weather_code_to_description(self, code):
        """Converte código WMO para descrição em português"""
        # Códigos WMO (World Meteorological Organization)
        weather_codes = {
            0: "Céu limpo ☀️",
            1: "Principalmente limpo 🌤️",
            2: "Parcialmente nublado ⛅",
            3: "Nublado ☁️",
            45: "Nevoeiro 🌫️",
            48: "Nevoeiro com geada 🌫️❄️",
            51: "Garoa leve 🌦️",
            53: "Garoa moderada 🌦️",
            55: "Garoa intensa 🌧️",
            61: "Chuva fraca 🌧️",
            63: "Chuva moderada 🌧️",
            65: "Chuva forte 🌧️🌊",
            71: "Neve fraca ❄️",
            73: "Neve moderada ❄️",
            75: "Neve forte ❄️🌨️",
            80: "Pancadas de chuva 🌦️",
            81: "Pancadas de chuva moderada 🌧️",
            82: "Pancadas de chuva violenta 🌧️🌊",
            95: "Tempestade ⛈️",
            96: "Tempestade com granizo pequeno ⛈️🧊",
            99: "Tempestade com granizo grande ⛈️🧊🧊"
        }
        return weather_codes.get(code, f"Condição {code} 🤷")
    
    def recomendar_guarda_chuva(self, linha_id):
        """Recomenda guarda-chuva baseado na previsão"""
        dados = self.get_previsao(linha_id)
        
        if not dados:
            return "❓ Não foi possível verificar chuva", "🤷"
        
        # Pega previsão de chuva
        daily = dados.get('daily', {})
        precip_sum = daily.get('precipitation_sum', [0])[0]
        precip_prob = daily.get('precipitation_probability_max', [0])[0]
        
        # Ajuste para linhas elevadas (ex: 15-Prata)
        if linha_id == "15" or LINHAS_POR_REGIAO.get(linha_id, {}).get('elevado', False):
            precip_sum *= 1.5
        
        if precip_sum >= 5 or precip_prob > 70:
            return f"🌧️ **LEVA GUARDA-CHUVA!** Probabilidade {precip_prob}% de chuva ({precip_sum:.1f}mm)", "☔"
        elif precip_sum >= 1 or precip_prob > 30:
            return f"🌦️ **Melhor levar**... Pode garoar ({precip_sum:.1f}mm, {precip_prob}%)", "☂️"
        else:
            return "☀️ **Pode deixar em casa**! Sem chuva prevista", "😎"
    
    def recomendar_blusa(self, linha_id):
        """Recomenda blusa baseado na temperatura"""
        dados = self.get_previsao(linha_id)
        
        if not dados:
            return "❓ Temperatura não disponível", "🤷"
        
        current = dados.get('current', {})
        daily = dados.get('daily', {})
        
        temp_atual = current.get('temperature_2m', 22)
        umidade = current.get('relative_humidity_2m', 65)
        weather_code = current.get('weather_code', 0)
        descricao = self.weather_code_to_description(weather_code)
        
        # Temperatura máxima e mínima do dia
        max_temp = daily.get('temperature_2m_max', [22])[0]
        min_temp = daily.get('temperature_2m_min', [18])[0]
        
        # Temperatura interna do metrô
        temp_metro = LINHAS_POR_REGIAO.get(linha_id, {}).get('temp_media_metro', 21)
        diferenca = abs(temp_atual - temp_metro)
        
        # Recomendação baseada na temperatura
        if temp_atual <= 15:
            msg = f"🥶 **CASACÃO PESADO!** Tá frio: {temp_atual}°C (mín {min_temp}°)"
            emoji = "🧥❄️"
        elif temp_atual <= 18:
            msg = f"🧥 **Leva blusa de frio** ({temp_atual}°C - {descricao})"
            emoji = "🧥"
        elif temp_atual <= 22:
            msg = f"👕 **Blusa leve** ({temp_atual}°C - {descricao})"
            emoji = "👕"
        elif temp_atual <= 28:
            msg = f"😎 **Roupa leve** ({temp_atual}°C)"
            emoji = "🩳"
        else:
            msg = f"🔥 **Calorão!** {temp_atual}°C - roupa bem fresca (máx {max_temp}°)"
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
        """Gera recomendação completa usando Open-Meteo API"""
        if linha_id not in LINHAS_POR_REGIAO:
            return None
        
        msg_chuva, emoji_chuva = self.recomendar_guarda_chuva(linha_id)
        msg_blusa, emoji_blusa = self.recomendar_blusa(linha_id)
        
        dados = self.get_previsao(linha_id)
        
        if dados:
            current = dados.get('current', {})
            daily = dados.get('daily', {})
            
            temp_atual = current.get('temperature_2m', '?')
            umidade = current.get('relative_humidity_2m', '?')
            vento = current.get('wind_speed_10m', '?')
            weather_code = current.get('weather_code', 0)
            descricao = self.weather_code_to_description(weather_code)
            
            max_temp = daily.get('temperature_2m_max', ['?'])[0]
            min_temp = daily.get('temperature_2m_min', ['?'])[0]
            
            cidade = f"Linha {linha_id} - {LINHAS_POR_REGIAO[linha_id]['bairros'][0]}"
        else:
            cidade = "São Paulo"
            temp_atual = "?"
            descricao = ""
            umidade = "?"
            vento = "?"
            max_temp = "?"
            min_temp = "?"
        
        mensagem = f"""
🚇 *Recomendação para {LINHAS_POR_REGIAO[linha_id]['nome']}*

📍 *Região:* {cidade}
🌡️ *Agora:* {temp_atual}°C - {descricao}
📊 *Máx/Mín:* {max_temp}° / {min_temp}°
💧 *Umidade:* {umidade}% | 🌬️ *Vento:* {vento} km/h

🌤️ *Recomendações:*
{msg_chuva}
{msg_blusa}

---
💡 *Linha:* {LINHAS_POR_REGIAO[linha_id]['nome']}
🕐 *Atualizado:* {get_sp_time()}
⚡ Dados via Open-Meteo (gratuito, sem token)
"""
        return mensagem
    
    def gerar_previsao_5dias(self, linha_id):
        """Gera previsão resumida para 5 dias"""
        if linha_id not in LINHAS_POR_REGIAO:
            return None
        
        dados = self.get_previsao(linha_id)
        
        if not dados:
            return "❌ Não foi possível buscar previsão"
        
        daily = dados.get('daily', {})
        cidade = f"Linha {linha_id}"
        
        msg = f"📅 *Previsão 5 dias - {cidade}*\n\n"
        
        # Lista de dias da semana em português
        dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        
        for i in range(5):
            try:
                data = daily.get('time', [''])[i]
                if data:
                    # Converte data para formato brasileiro
                    data_obj = datetime.strptime(data, "%Y-%m-%d")
                    data_formatada = data_obj.strftime("%d/%m")
                    dia_semana = dias_semana[data_obj.weekday()]
                else:
                    data_formatada = f"Dia {i+1}"
                    dia_semana = ""
                
                max_temp = daily.get('temperature_2m_max', [0])[i]
                min_temp = daily.get('temperature_2m_min', [0])[i]
                chuva = daily.get('precipitation_sum', [0])[i]
                prob = daily.get('precipitation_probability_max', [0])[i]
                weather_code = daily.get('weather_code', [0])[i]
                desc = self.weather_code_to_description(weather_code)
                
                msg += f"*{data_formatada} ({dia_semana})*\n"
                msg += f"🌡️ {min_temp}° ~ {max_temp}° | 🌧️ {chuva}mm ({prob}%)\n"
                msg += f"📝 {desc}\n\n"
            except:
                pass
        
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
    clima = OpenMeteoAPI()
    for linha_id in linhas_alertar:
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
                    send_telegram_message(chat_id, "🔍 Consultando clima em tempo real...")
                    
                    clima = OpenMeteoAPI()
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
                send_telegram_message(chat_id, "🔍 Buscando previsão...")
                
                clima = OpenMeteoAPI()
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

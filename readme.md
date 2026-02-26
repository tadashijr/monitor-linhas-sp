# 🚇 Monitor Linhas SP v2.0 - Bot do Telegram

Bot inteligente que monitora o status das linhas do Metrô/CPTM de São Paulo **e ainda recomenda se levar guarda-chuva ou blusa** baseado no clima da sua linha!

[![GitHub Workflow Status](https://img.shields.io/badge/GitHub%20Actions-Automação-blue)](https://github.com/SEU_USUARIO/monitor-linhas-sp/actions)
[![Render](https://img.shields.io/badge/Render-Deploy-success)](https://render.com)
[![Telegram Bot](https://img.shields.io/badge/Telegram-@MonitorLinhasSP__bot-blue)](https://t.me/MonitorLinhasSP_bot)
[![Python](https://img.shields.io/badge/Python-3.10-yellow)](https://python.org)
[![Open-Meteo](https://img.shields.io/badge/Clima-Open--Meteo-green)](https://open-meteo.com)
[![Version](https://img.shields.io/badge/versão-2.0-brightgreen)]()

---

## 📋 **SUMÁRIO**

- [Novidades da v2.0](#-novidades-da-v20)
- [Sobre o Projeto](#-sobre-o-projeto)
- [Arquitetura da Solução](#-arquitetura-da-solução)
- [Funcionalidades](#-funcionalidades)
- [Comandos do Bot](#-comandos-do-bot)
- [Linhas Monitoradas](#-linhas-monitoradas)
- [Clima Inteligente por Linha](#-clima-inteligente-por-linha)
- [Configuração](#-configuração)
- [Implantação no Render](#-implanta%C3%A7%C3%A3o-no-render)
- [Manter Bot Acordado](#-manter-bot-acordado-cron-job)
- [Arquivos do Projeto](#-arquivos-do-projeto)
- [Solução de Problemas](#-solu%C3%A7%C3%A3o-de-problemas)
- [Licença](#-licença)

---

## ✨ **NOVIDADES DA V2.0**

| Funcionalidade | Descrição |
|----------------|-----------|
| 🌤️ **Clima inteligente por linha** | Recomendação personalizada baseada na localização exata de cada linha |
| ☔ **Alerta de guarda-chuva** | "Leva ou não leva?" com base na previsão de chuva |
| 🧥 **Recomendação de blusa** | Baseado na temperatura + sensação térmica + contraste com o metrô |
| 📍 **Microclima por estação** | Considera estações arborizadas como Trianon-Masp |
| 🚆 **Temperatura interna do metrô** | Dados reais de cada linha (pesquisa Folha de SP) |
| 🔄 **API 100% gratuita** | Open-Meteo - sem token, sem cadastro, sem limites |
| 📊 **Previsão de 5 dias** | Para planejar a semana |

---

## 📋 **SOBRE O PROJETO**

Este bot monitora o status operacional das linhas do Metrô e CPTM de São Paulo, utilizando **duas estratégias complementares** e agora com **inteligência climática personalizada**.

### 🤔 **O problema que resolve**
- ⏰ Perder tempo com imprevistos no metrô
- 🌧️ Ser pego de surpresa pela chuva
- 🥶 Passar frio ou calor por não saber a temperatura
- 🚆 Não saber se o ar-condicionado do metrô é forte

### 💡 **A solução**
Um bot que **pensa por você**: avisa o status do metrô **E** recomenda o que vestir/levar!

---

## 🏗️ **ARQUITETURA DA SOLUÇÃO**

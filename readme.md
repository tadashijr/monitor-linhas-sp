# 🚇 Monitor Linhas SP - Bot do Telegram

Bot automático para monitorar o status das linhas do Metrô/CPTM de São Paulo, com notificações agendadas e comandos interativos.

![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automa%C3%A7%C3%A3o-blue)
![Render](https://img.shields.io/badge/Render-Deploy-success)
![Telegram](https://img.shields.io/badge/Telegram-@MonitorLinhasSP__bot-blue)
![Python](https://img.shields.io/badge/Python-3.10-yellow)
![Cron-job](https://img.shields.io/badge/Cron--job-Ativo-brightgreen)

---

## 📋 SUMÁRIO

- [Sobre o Projeto](#-sobre-o-projeto)
- [Arquitetura da Solução](#-arquitetura-da-solução)
- [Funcionalidades](#-funcionalidades)
- [Como Funciona](#-como-funciona)
- [Comandos do Bot](#-comandos-do-bot)
- [Linhas Monitoradas](#-linhas-monitoradas)
- [Configuração](#-configuração)
- [Implantação no Render](#-implantação-no-render)
- [Manter Bot Acordado](#-manter-bot-acordado-cron-job)
- [Monitoramento](#-monitoramento)

---

## 📋 SOBRE O PROJETO

Este bot monitora o status operacional das linhas do Metrô e CPTM de São Paulo, utilizando duas estratégias complementares para garantir que você nunca seja pego de surpresa com problemas no transporte público.

### 🎯 Objetivo

Fornecer informações atualizadas sobre o funcionamento das linhas, tanto por notificações automáticas em horários estratégicos quanto por consulta sob demanda através de comandos.

---

## 🏗️ ARQUITETURA DA SOLUÇÃO

```
┌─────────────────────────────────────────────────────────────────┐
│                         TELEGRAM BOT                            │
│                    @MonitorLinhasSP_bot                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────────┐                 ┌───────────────────┐
│  GITHUB ACTIONS   │                 │      RENDER       │
│   (Automático)    │                 │    (Interativo)   │
├───────────────────┤                 ├───────────────────┤
│ ✓ Roda 3x ao dia  │                 │ ✓ 24/7 online     │
│ ✓ 07:00 BRT       │                 │ ✓ Webhook Telegram│
│ ✓ 17:00 BRT       │                 │ ✓ Resposta imediata│
│ ✓ 22:00 BRT       │                 │ ✓ Flask + Gunicorn│
│ ✓ Gratuito        │                 │ ✓ Free tier       │
└─────────┬─────────┘                 └─────────┬─────────┘
          │                                       │
          └───────────────┬───────────────────────┘
                          ▼
               ┌─────────────────────────┐
               │      CRON-JOB.ORG       │
               │       (Keep Alive)      │
               ├─────────────────────────┤
               │ ✓ Ping a cada 10min     │
               │ ✓ Mantém bot acordado   │
               │ ✓ Gratuito              │
               └────────────┬────────────┘
                            ▼
               ┌─────────────────────────┐
               │       SITE ARTESP       │
               │   Status das linhas     │
               └─────────────────────────┘
```

---

## ✨ FUNCIONALIDADES

| Funcionalidade | Descrição | Onde roda |
|---------------|-----------|-----------|
| ✅ Notificações automáticas | Envia status às 7h, 17h e 22h | GitHub Actions |
| ✅ Comandos interativos | Responde a `/linha 2`, `/todos` | Render |
| ✅ Alertas seletivos | Opção de notificar apenas falhas | Ambos |
| ✅ Todas as linhas | Monitora as 13 linhas do sistema | Ambos |
| ✅ Keep-alive | Mantém bot acordado 24/7 | Cron-job.org |
| ✅ Histórico completo | Logs de todas as execuções | GitHub Actions |
| ✅ Gratuito | 100% sem custo | Todos serviços |

---

## ⚙️ COMO FUNCIONA

### 🔄 Fluxo de Funcionamento

- Usuário envia comando → Webhook no Render → Bot consulta site da ARTESP → Resposta imediata  
- Horário programado → GitHub Actions executa → Bot consulta site → Envia notificação  
- Sem atividade → Cron-job ping a cada 10min → Render mantém processo ativo  

### ⏰ Horários das Notificações

| Horário (BRT) | Propósito |
|---------------|-----------|
| 07:00 | Antes de sair para o trabalho |
| 17:00 | Horário de pico da volta |
| 22:00 | Planejamento do dia seguinte |

---

## 🤖 COMANDOS DO BOT

### 📱 Comandos Disponíveis

| Comando | Descrição |
|----------|-----------|
| `/start` | Mensagem de boas-vindas |
| `/linha [número]` | Status de uma linha específica |
| `/todos` | Status de todas as linhas |

### 💬 Exemplo

**Comando:** `/linha 2`

```
🚇 Status da Linha 2-Verde

📊 Status: ✅ Operação Normal
🏢 Operadora: Metrô
🕐 Consultado: 15/02/2026 22:01:23
```

---

## 🚇 LINHAS MONITORADAS

| ID | Linha | Operadora |
|----|--------|------------|
| 1 | Linha 1-Azul | Metrô |
| 2 | Linha 2-Verde | Metrô |
| 3 | Linha 3-Vermelha | Metrô |
| 4 | Linha 4-Amarela | ViaQuatro |
| 5 | Linha 5-Lilás | ViaMobilidade |
| 7 | Linha 7-Rubi | CPTM |
| 8 | Linha 8-Diamante | ViaMobilidade |
| 9 | Linha 9-Esmeralda | ViaMobilidade |
| 10 | Linha 10-Turquesa | CPTM |
| 11 | Linha 11-Coral | CPTM |
| 12 | Linha 12-Safira | CPTM |
| 13 | Linha 13-Jade | CPTM |
| 15 | Linha 15-Prata | Metrô |

---

## 🔧 CONFIGURAÇÃO

### 📋 Pré-requisitos

- Conta no GitHub  
- Conta no Render  
- Conta no cron-job.org  
- Bot criado no Telegram via @BotFather  

---

## 🔐 Variáveis de Ambiente

### GitHub Secrets

| Nome | Descrição |
|------|-----------|
| TELEGRAM_TOKEN | Token do bot |
| CHAT_ID | Seu ID no Telegram |
| ALERTAR_FALHA | true ou false |

### Render

| Nome | Valor |
|------|--------|
| TELEGRAM_TOKEN | Seu token |
| CHAT_ID | Seu ID |
| ALERTAR_FALHA | true |
| PYTHON_VERSION | 3.10.12 |

---

## 🚀 IMPLANTAÇÃO NO RENDER

### 📦 Via Blueprint (Recomendado)

1. Faça push para o GitHub  
2. No Render → New + → Blueprint  
3. Conecte o repositório  
4. Configure variáveis  
5. Apply  

### 🖥️ Via Web Service

- Build Command: `pip install -r requirements.txt`  
- Start Command: `gunicorn main:app`  
- Plan: Free  

---

## ⏰ MANTER BOT ACORDADO (CRON-JOB)

### Configuração

- URL: `https://seu-app.onrender.com/healthz`
- Execução: Every 10 minutes

---

## 📊 MONITORAMENTO

### GitHub Actions
- Aba Actions → Histórico completo
- Logs detalhados

### Render
- Logs em tempo real  
- Métricas  
- Histórico de deploy  

### Cron-job.org
- Dashboard  
- Estatísticas  
- Alertas por email  

---

## 📄 LICENÇA

Este projeto é de uso livre para fins educacionais e pessoais.

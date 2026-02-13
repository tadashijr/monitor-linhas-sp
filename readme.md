🚇 Monitor Linhas SP - Bot do Telegram
Bot do Telegram para monitoramento automático do status das linhas 2-Verde e 15-Prata do Metrô de São Paulo.

📋 Sobre o Projeto
Este bot verifica automaticamente o site da ARTESP duas vezes ao dia (7h e 17h) e envia notificações no Telegram sobre o status operacional das linhas monitoradas.

✨ Funcionalidades
✅ Verificação automática todos os dias às 7h e 17h

✅ Monitoramento das linhas 2-Verde e 15-Prata

✅ Alertas apenas quando há mudança no status (opcional)

✅ Histórico completo de verificações via GitHub Actions

✅ Fácil de expandir para monitorar mais linhas

🚀 Como Usar
Pré-requisitos
Conta no GitHub (gratuita)

Conta no Telegram

Token de um bot do Telegram (criado via @BotFather)

Configuração Rápida
Crie seu bot no Telegram via @BotFather e guarde o token

Use este template clicando em "Use this template" acima

Configure os segredos no seu repositório (Settings → Secrets and variables → Actions):

TELEGRAM_TOKEN: token do seu bot

CHAT_ID: seu ID de usuário no Telegram

WEBSITES: configuração das linhas a monitorar (ver exemplo abaixo)

Ative o GitHub Actions na aba Actions do repositório

Exemplo de Configuração
Secret WEBSITES:

json
[
  {
    "name": "Linha 2-Verde",
    "url": "https://ccm.artesp.sp.gov.br/metroferroviario/status-linhas/",
    "validation_text": "Operação Normal",
    "validation_type": "text"
  },
  {
    "name": "Linha 15-Prata",
    "url": "https://ccm.artesp.sp.gov.br/metroferroviario/status-linhas/",
    "validation_text": "Operação Normal",
    "validation_type": "text"
  }
]
⚙️ Personalização
Ajustar Horários
Edite o arquivo .github/workflows/checker.yml:

yaml
schedule:
  - cron: '0 10,22 * * *'  # 7h e 17h (horário de Brasília)
Formato cron: minuto hora * * * (UTC)

Adicionar Mais Linhas
Basta incluir novos itens no JSON do secret WEBSITES:

json
{
  "name": "Linha 1-Azul",
  "url": "https://ccm.artesp.sp.gov.br/metroferroviario/status-linhas/",
  "validation_text": "Operação Normal",
  "validation_type": "text"
}
Notificações Seletivas
No arquivo main.py, altere:

python
ALWAYS_NOTIFY = False  # True = notifica sempre, False = só em mudanças
📊 Monitoramento
Acesse a aba Actions para ver o histórico de execuções

Clique em qualquer execução para ver os logs detalhados

O GitHub envia email automático em caso de falha

🔧 Solução de Problemas
Não recebo notificações
Verifique se mandou /start para o bot no Telegram

Confirme se o CHAT_ID está correto

Veja os logs em Actions → última execução

Site mudou de formato
Se o site da ARTESP for atualizado, pode ser necessário ajustar os seletores no arquivo main.py.

📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

🤝 Contribuições
Contribuições são bem-vindas! Sinta-se à vontade para:

Reportar bugs

Sugerir novas funcionalidades

Enviar pull requests

📬 Contato
Bot no Telegram: @MonitorLinhasSP_bot

Issues: Abra uma issue neste repositório

Desenvolvido com ❤️ para facilitar a vida dos usuários do Metrô de São Paulo

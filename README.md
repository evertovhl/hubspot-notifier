# HubSpot Notifier

Verifica a cada 5 minutos se há chamados (tickets) novos no HubSpot e envia um
aviso para um chat/grupo do Telegram. Roda de graça no GitHub Actions
(repositório público = minutos ilimitados).

## Como funciona

1. Um workflow agendado (`.github/workflows/check-tickets.yml`) roda a cada 5 min.
2. `scripts/check_tickets.py` consulta a API do HubSpot por tickets criados
   depois do último check (guardado em `state/last_check.txt`).
3. Para cada ticket novo, envia uma mensagem para o Telegram.
4. O workflow commita o novo timestamp de volta no repositório.

## Passo a passo para configurar

### 1. Criar um Private App no HubSpot

1. No HubSpot: **Configurações → Integrações → Private Apps → Criar app privada**.
2. Na aba **Scopes**, marque `crm.objects.tickets.read`.
3. Crie e copie o **Access Token** gerado (começa com `pat-...`).

### 2. Criar o bot do Telegram

1. No Telegram, abra uma conversa com **@BotFather**.
2. Envie `/newbot`, escolha um nome e um username (precisa terminar em `bot`).
3. Copie o **token** que ele te der.
4. Adicione o bot ao grupo/canal onde quer receber os avisos (ou converse
   diretamente com ele, se for notificação pessoal).

### 3. Descobrir o Chat ID do Telegram

1. Envie qualquer mensagem no grupo/chat onde o bot foi adicionado.
2. Acesse no navegador:
   `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
3. Procure o campo `"chat":{"id": ...}` na resposta — esse é o `TELEGRAM_CHAT_ID`
   (para grupos costuma ser um número negativo).

### 4. Publicar este repositório no GitHub

Crie um repositório **público** vazio no GitHub e faça o push desta pasta:

```bash
git init
git add .
git commit -m "chore: setup hubspot to telegram ticket notifier"
git branch -M main
git remote add origin <URL_DO_SEU_REPO>
git push -u origin main
```

### 5. Configurar os Secrets no GitHub

No repositório: **Settings → Secrets and variables → Actions → New repository secret**.
Crie:

| Nome | Valor |
|---|---|
| `HUBSPOT_TOKEN` | Access token do Private App (passo 1) |
| `TELEGRAM_BOT_TOKEN` | Token do bot (passo 2) |
| `TELEGRAM_CHAT_ID` | Chat ID (passo 3) |
| `HUBSPOT_PORTAL_ID` | (opcional) ID da sua conta HubSpot, para incluir link direto ao ticket na mensagem |

### 6. Testar

Vá em **Actions → HubSpot Notifier → Run workflow** para
disparar manualmente e conferir se chega a mensagem no Telegram. Depois disso
ele roda solo a cada 5 minutos.

## Ponto de atenção

O nome da propriedade de data de criação do ticket usada no filtro é
`createdate` (padrão do objeto CRM). Se o teste manual retornar erro de
propriedade inválida, crie o secret opcional `HUBSPOT_DATE_PROPERTY` com o
nome correto (ex: `hs_createdate`).

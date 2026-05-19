# 🇮🇹 Italian Citizenship Case Monitor
### Monitor Automatizado de Processo de Cidadania Italiana

> **PT:** Automação que verifica diariamente atualizações em processos de cidadania italiana no site [laviaitalia.com.br](https://laviaitalia.com.br) e envia notificações por e-mail quando há mudanças.
>
> **EN:** Automation that daily checks for updates on Italian citizenship cases on [laviaitalia.com.br](https://laviaitalia.com.br) and sends email notifications when changes are detected.

---

## 🧠 Como funciona / How it works

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions (Cron)                       │
│                    Todo dia às 08:00 BRT                        │
│                   Every day at 08:00 BRT                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │       scraper.py        │
              │  Playwright + Chromium  │
              │  Acessa o site e lê     │
              │  os dados do processo   │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │        state.py         │
              │  Compara com state.json │
              │  (salvo no repositório) │
              │  Detecta mudanças       │
              └────────────┬────────────┘
                           │
           ┌───────────────┴──────────────┐
           │                              │
    Sem mudanças               Mudanças detectadas
    No changes                 Changes detected
           │                              │
    Atualiza state.json        notifier.py → E-mail
    Updates state.json         + Atualiza state.json
```

---

## 🛠️ Stack técnica / Tech stack

| Ferramenta / Tool | Função / Purpose |
|---|---|
| **Python 3.11** | Linguagem principal / Main language |
| **Playwright** | Automação de navegador (contorna Cloudflare Turnstile) / Browser automation (bypasses Cloudflare Turnstile) |
| **GitHub Actions** | Agendador de tarefas gratuito na nuvem / Free cloud task scheduler |
| **smtplib** | Envio de e-mail via Gmail SMTP / Email sending via Gmail SMTP |
| **GitHub Secrets** | Armazenamento seguro de credenciais / Secure credentials storage |
| **JSON** | Persistência de estado entre execuções / State persistence between runs |

---

## 📂 Estrutura do projeto / Project structure

```
processo-cidadania-monitor/
│
├── .github/
│   └── workflows/
│       └── monitor.yml      # Agendamento e orquestração / Scheduling & orchestration
│
├── main.py                  # Ponto de entrada / Entry point
├── scraper.py               # Acessa o site e extrai dados / Accesses site & extracts data
├── state.py                 # Gerencia estado persistido / Manages persisted state
├── notifier.py              # Envia e-mail de notificação / Sends notification email
│
├── state.json               # Estado atual do processo (auto-gerado) / Current case state (auto-generated)
├── requirements.txt         # Dependências Python / Python dependencies
├── .env.example             # Template de variáveis de ambiente / Environment variables template
├── .gitignore
└── README.md
```

---

## ⚙️ Configuração passo a passo / Step-by-step setup

### Passo 1 — Fork ou clone o repositório / Fork or clone the repository

```bash
git clone https://github.com/SEU_USUARIO/processo-cidadania-monitor.git
cd processo-cidadania-monitor
```

> **PT:** Se quiser colocar no seu GitHub, faça um fork antes.
> **EN:** If you want it on your GitHub, fork it first.

---

### Passo 2 — Configure o ambiente local / Set up local environment

```bash
# PT: Crie um ambiente virtual (boa prática)
# EN: Create a virtual environment (best practice)
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

# PT: Instale as dependências
# EN: Install dependencies
pip install -r requirements.txt

# PT: Instale o Chromium para o Playwright
# EN: Install Chromium for Playwright
playwright install chromium
```

---

### Passo 3 — Crie sua Senha de App do Google / Create your Google App Password

> **PT:** O Gmail não permite login com senha normal por scripts. Você precisa de uma **Senha de App** — uma senha separada gerada especificamente para este projeto.
>
> **EN:** Gmail doesn't allow login with a regular password from scripts. You need an **App Password** — a separate password generated specifically for this project.

1. Acesse / Go to: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. **PT:** Clique em "Criar senha de app" → dê o nome "Citizenship Monitor" → copie a senha de 16 caracteres
   **EN:** Click "Create App Password" → name it "Citizenship Monitor" → copy the 16-character password
3. **⚠️ Requisito:** Verificação em 2 etapas deve estar ativa na sua conta Google / 2-step verification must be active on your Google account

---

### Passo 4 — Crie o arquivo .env local / Create local .env file

```bash
cp .env.example .env
```

Edite o `.env` com seus dados reais / Edit `.env` with your real data:

```env
GMAIL_USER=seu_email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
NOTIFY_EMAIL=seu_email@gmail.com
CASE_NUMBER=XXXX
CASE_YEAR=XXXX
```

---

### Passo 5 — Teste localmente / Test locally

```bash
python main.py
```

**PT:** Na primeira execução:
- O Chromium vai abrir (em modo headless, sem janela)
- Vai preencher o formulário e ler os dados
- Vai criar o `state.json`
- Vai enviar um e-mail de confirmação "Monitor Ativo"

**EN:** On the first run:
- Chromium will open (headless, no visible window)
- It will fill the form and read the data
- It will create `state.json`
- It will send a confirmation email "Monitor Active"

---

### Passo 6 — Configure os GitHub Secrets / Configure GitHub Secrets

> **PT:** Os Secrets são variáveis de ambiente criptografadas armazenadas no GitHub. O código nunca vê os valores reais — o GitHub os injeta no momento da execução.
>
> **EN:** Secrets are encrypted environment variables stored on GitHub. The code never sees the real values — GitHub injects them at runtime.

1. No seu repositório no GitHub, vá em / In your GitHub repository, go to:
   **Settings → Secrets and variables → Actions → New repository secret**

2. Crie os seguintes secrets / Create the following secrets:

| Secret Name | Valor / Value |
|---|---|
| `GMAIL_USER` | seu_email@gmail.com |
| `GMAIL_APP_PASSWORD` | senha de app de 16 dígitos / 16-digit app password |
| `NOTIFY_EMAIL` | e-mail que receberá notificações / email to receive notifications |
| `CASE_NUMBER` | `3702` |
| `CASE_YEAR` | `2024` |

---

### Passo 7 — Ative o workflow / Enable the workflow

**PT:** Após o primeiro `git push`, vá em **Actions** no seu repositório e clique em **"I understand my workflows, go ahead and enable them"** se solicitado.

**EN:** After the first `git push`, go to **Actions** in your repository and click **"I understand my workflows, go ahead and enable them"** if prompted.

**PT:** Para testar imediatamente sem esperar o cron:
**EN:** To test immediately without waiting for cron:

1. Vá em / Go to: **Actions → 🇮🇹 Italian Citizenship Case Monitor**
2. Clique em / Click: **Run workflow → Run workflow**

---

## 📧 Exemplos de e-mail / Email examples

**Primeira execução / First run:**
> ✅ **[Monitor Ativo] Processo 3702/2024 — Sem alterações**
> O monitoramento diário está configurado e funcionando.

**Quando há atualização / When there's an update:**
> 🔔 **[ATUALIZAÇÃO] Processo 3702/2024 — 1 mudança(s)**
> Status: ATTESA DEPOSITO NOTE IN SOSTITUZIONE UDIENZA → [NOVO STATUS]

---

## 🔍 Decisões técnicas / Technical decisions

### Por que Playwright e não `requests`?
O site usa **Cloudflare Turnstile** (um CAPTCHA invisível moderno). Requisições HTTP simples são bloqueadas. O Playwright simula um navegador Chromium real, passando pela verificação automaticamente.

*The site uses **Cloudflare Turnstile** (a modern invisible CAPTCHA). Plain HTTP requests are blocked. Playwright simulates a real Chromium browser, passing the check automatically.*

### Por que `state.json` no repositório?
O GitHub Actions não tem memória entre execuções — cada run começa do zero. Ao commitar o `state.json` de volta ao repositório, criamos uma memória persistente gratuita. Como bônus, o histórico de commits funciona como um log de auditoria das mudanças do processo.

*GitHub Actions has no memory between runs — each run starts fresh. By committing `state.json` back to the repository, we create free persistent memory. As a bonus, the commit history works as an audit log of case changes.*

### Por que Gmail App Password e não OAuth?
OAuth exige um servidor de redirecionamento e credenciais de aplicativo OAuth registradas. A App Password é mais simples para automações pessoais e igualmente segura quando armazenada em Secrets.

*OAuth requires a redirect server and registered OAuth app credentials. App Password is simpler for personal automations and equally secure when stored in Secrets.*

---

## 📄 Licença / License

MIT — sinta-se livre para usar, modificar e distribuir.
*MIT — feel free to use, modify, and distribute.*

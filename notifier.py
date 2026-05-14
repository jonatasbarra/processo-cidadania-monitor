"""
notifier.py
===========
PT: Envia notificações por e-mail via Gmail usando SMTP com TLS.
    Usa variáveis de ambiente para não expor credenciais no código.

EN: Sends email notifications via Gmail using SMTP with TLS.
    Uses environment variables to avoid exposing credentials in code.

Segurança / Security:
  PT: NUNCA coloque sua senha diretamente no código.
      Use GitHub Secrets (explicado no README) para injetar as
      variáveis de ambiente GMAIL_USER e GMAIL_APP_PASSWORD.
  EN: NEVER put your password directly in the code.
      Use GitHub Secrets (explained in README) to inject the
      environment variables GMAIL_USER and GMAIL_APP_PASSWORD.
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dataclasses import asdict

from scraper import CaseSnapshot

logger = logging.getLogger(__name__)


def send_email_notification(snapshot: CaseSnapshot, changes: list[dict]) -> None:
    """
    PT: Envia um e-mail formatado com as mudanças detectadas no processo.
        Se não houver mudanças (primeira execução), envia confirmação
        de que o monitoramento está ativo.

    EN: Sends a formatted email with detected case changes.
        If there are no changes (first run), sends confirmation
        that monitoring is active.
    """
    gmail_user     = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient      = os.environ.get("NOTIFY_EMAIL", gmail_user)

    # PT: Monta assunto dinâmico conforme tipo de notificação
    # EN: Build dynamic subject based on notification type
    if not changes:
        subject = f"✅ [Monitor Ativo] Processo {snapshot.case_number} — Sem alterações"
        html_body = _build_first_run_html(snapshot)
    else:
        subject = f"🔔 [ATUALIZAÇÃO] Processo {snapshot.case_number} — {len(changes)} mudança(s)"
        html_body = _build_changes_html(snapshot, changes)

    # -----------------------------------------------------------------------
    # PT: Configura a mensagem MIME (suporte a HTML + texto simples)
    # EN: Configure the MIME message (HTML + plain text fallback)
    # -----------------------------------------------------------------------
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = gmail_user
    msg["To"]      = recipient

    # PT: Versão texto simples como fallback para clientes sem HTML
    # EN: Plain text fallback for clients without HTML support
    plain = _html_to_plain(snapshot, changes)
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # -----------------------------------------------------------------------
    # PT: Envia via SMTP do Gmail com STARTTLS (porta 587)
    # EN: Send via Gmail SMTP with STARTTLS (port 587)
    # -----------------------------------------------------------------------
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipient, msg.as_string())

    logger.info("Email sent to %s", recipient)


# ---------------------------------------------------------------------------
# PT: Funções auxiliares de construção de HTML
# EN: HTML building helper functions
# ---------------------------------------------------------------------------

def _build_changes_html(snapshot: CaseSnapshot, changes: list[dict]) -> str:
    changes_rows = ""
    field_labels = {
        "status": "Status",
        "last_historical_record": "Último Registro / Last Record",
        "queue_position": "Posição na Fila / Queue Position",
        "raw_timeline": "Timeline",
    }
    for ch in changes:
        label = field_labels.get(ch["field"], ch["field"])
        old_val = ch["old"] if not isinstance(ch["old"], list) else "<br>".join(ch["old"])
        new_val = ch["new"] if not isinstance(ch["new"], list) else "<br>".join(ch["new"])
        changes_rows += f"""
        <tr>
          <td style="padding:8px;font-weight:bold;color:#555">{label}</td>
          <td style="padding:8px;color:#c0392b;text-decoration:line-through">{old_val}</td>
          <td style="padding:8px;color:#27ae60;font-weight:bold">{new_val}</td>
        </tr>"""

    return f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:640px;margin:auto">
      <div style="background:#1a3a5c;color:white;padding:24px;border-radius:8px 8px 0 0">
        <h1 style="margin:0;font-size:22px">🔔 Atualização no Processo</h1>
        <p style="margin:4px 0 0;opacity:.8">Processo {snapshot.case_number} — Ordinary Court of L'Aquila</p>
      </div>
      <div style="border:1px solid #ddd;border-top:none;padding:24px;border-radius:0 0 8px 8px">
        <h2 style="color:#1a3a5c">Status atual / Current status</h2>
        <p style="background:#eaf4fb;padding:12px;border-radius:6px;font-size:16px;font-weight:bold">
          {snapshot.status}
        </p>
        <h2 style="color:#1a3a5c">Mudanças detectadas / Detected changes</h2>
        <table style="width:100%;border-collapse:collapse">
          <thead>
            <tr style="background:#f5f5f5">
              <th style="padding:8px;text-align:left">Campo / Field</th>
              <th style="padding:8px;text-align:left">Antes / Before</th>
              <th style="padding:8px;text-align:left">Depois / After</th>
            </tr>
          </thead>
          <tbody>{changes_rows}</tbody>
        </table>
        <p style="margin-top:24px;font-size:12px;color:#999">
          Verificação automática em {snapshot.last_check} •
          <a href="https://laviaitalia.com.br/processo-de-cidadania/consultar-processo">Ver processo</a>
        </p>
      </div>
    </body></html>"""


def _build_first_run_html(snapshot: CaseSnapshot) -> str:
    timeline_items = "".join(f"<li>{e}</li>" for e in snapshot.raw_timeline)
    return f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:640px;margin:auto">
      <div style="background:#27ae60;color:white;padding:24px;border-radius:8px 8px 0 0">
        <h1 style="margin:0;font-size:22px">✅ Monitor Ativo / Monitor Active</h1>
        <p style="margin:4px 0 0;opacity:.8">Processo {snapshot.case_number} — Ordinary Court of L'Aquila</p>
      </div>
      <div style="border:1px solid #ddd;border-top:none;padding:24px;border-radius:0 0 8px 8px">
        <p>O monitoramento diário está configurado e funcionando.<br>
           <em>Daily monitoring is set up and running.</em></p>
        <h2 style="color:#1a3a5c">Status atual / Current status</h2>
        <p style="background:#eaf4fb;padding:12px;border-radius:6px;font-weight:bold">{snapshot.status}</p>
        <h2 style="color:#1a3a5c">Timeline</h2>
        <ul style="line-height:1.8">{timeline_items}</ul>
        <p style="font-size:12px;color:#999">
          Verificação em {snapshot.last_check} •
          <a href="https://laviaitalia.com.br/processo-de-cidadania/consultar-processo">Ver processo</a>
        </p>
      </div>
    </body></html>"""


def _html_to_plain(snapshot: CaseSnapshot, changes: list[dict]) -> str:
    if not changes:
        return (
            f"Monitor ativo | Processo {snapshot.case_number}\n"
            f"Status: {snapshot.status}\n"
            f"Verificado em: {snapshot.last_check}\n"
        )
    lines = [f"ATUALIZAÇÃO — Processo {snapshot.case_number}", f"Status: {snapshot.status}", ""]
    for ch in changes:
        lines.append(f"[{ch['field']}]  {ch['old']}  →  {ch['new']}")
    return "\n".join(lines)

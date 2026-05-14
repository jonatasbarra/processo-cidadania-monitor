"""
main.py
=======
PT: Ponto de entrada da automação. Orquestra as três etapas:
      1. Buscar estado atual do processo (scraper.py)
      2. Comparar com estado anterior (state.py)
      3. Notificar se houver mudanças (notifier.py)

EN: Automation entry point. Orchestrates three steps:
      1. Fetch current case state (scraper.py)
      2. Compare with previous state (state.py)
      3. Notify if there are changes (notifier.py)

Uso / Usage:
  python main.py
  python main.py --case 3702 --year 2024   # sobrescreve .env / overrides .env
"""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from scraper import fetch_case_snapshot
from state import load_previous_snapshot, save_snapshot, detect_changes
from notifier import send_email_notification

# ---------------------------------------------------------------------------
# PT: Configuração de logging — imprime data/hora, nível e mensagem.
#     No GitHub Actions, esses logs aparecem na aba "Actions" do repositório.
# EN: Logging setup — prints date/time, level, and message.
#     In GitHub Actions, these logs appear in the repository's "Actions" tab.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PT: Monitor de processo de cidadania italiana | EN: Italian citizenship case monitor"
    )
    parser.add_argument("--case", help="Número do processo / Case number (default: env CASE_NUMBER)")
    parser.add_argument("--year", help="Ano do processo / Case year (default: env CASE_YEAR)")
    parser.add_argument(
        "--force-notify",
        action="store_true",
        help="PT: Envia e-mail mesmo sem mudanças | EN: Send email even without changes",
    )
    return parser.parse_args()


def main() -> None:
    # PT: Carrega variáveis do arquivo .env (só funciona localmente;
    #     no GitHub Actions as variáveis vêm dos Secrets)
    # EN: Load variables from .env file (local only;
    #     in GitHub Actions variables come from Secrets)
    load_dotenv()

    args = parse_args()

    case_number = args.case or os.environ.get("CASE_NUMBER", "3702")
    year        = args.year or os.environ.get("CASE_YEAR", "2024")

    logger.info("═" * 60)
    logger.info("Starting monitor for case %s/%s", case_number, year)
    logger.info("═" * 60)

    # ── Step 1 / Passo 1 ────────────────────────────────────────────────────
    logger.info("[1/3] Fetching current case snapshot…")
    try:
        current = fetch_case_snapshot(case_number, year)
    except Exception as exc:
        logger.error("Failed to fetch case data: %s", exc)
        sys.exit(1)

    logger.info("Status: %s", current.status)
    logger.info("Last record: %s", current.last_historical_record)

    # ── Step 2 / Passo 2 ────────────────────────────────────────────────────
    logger.info("[2/3] Comparing with previous state…")
    previous = load_previous_snapshot()
    changes  = detect_changes(previous, current)

    if changes:
        logger.info("🔔 %d change(s) detected!", len(changes))
    else:
        logger.info("✅ No changes detected.")

    # ── Step 3 / Passo 3 ────────────────────────────────────────────────────
    logger.info("[3/3] Sending notification…")
    should_notify = bool(changes) or previous is None or args.force_notify

    if should_notify:
        try:
            send_email_notification(current, changes)
        except Exception as exc:
            logger.error("Failed to send email: %s", exc)
            # PT: Salva o estado mesmo se o e-mail falhar
            # EN: Save state even if email fails

    # PT: Sempre salva o estado atual para a próxima execução
    # EN: Always save current state for the next run
    save_snapshot(current)

    logger.info("Done. State saved.")
    logger.info("═" * 60)


if __name__ == "__main__":
    main()

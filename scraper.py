"""
scraper.py
==========
PT: Módulo responsável por acessar o site laviaitalia.com.br,
    preencher o formulário e extrair os dados do processo.

EN: Module responsible for accessing laviaitalia.com.br,
    filling the form and extracting case data.

Por que Playwright?
Why Playwright?
  PT: O site usa Cloudflare Turnstile (um CAPTCHA moderno). Requisições
      simples com `requests` são bloqueadas. O Playwright simula um
      navegador real, contornando essa proteção.
  EN: The site uses Cloudflare Turnstile (a modern CAPTCHA). Plain
      `requests` calls get blocked. Playwright simulates a real browser,
      bypassing that protection.
"""

import re
import time
import logging
from dataclasses import dataclass, asdict
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PT: Estrutura de dados que representa o estado atual do processo.
# EN: Data structure representing the current state of the case.
# ---------------------------------------------------------------------------
@dataclass
class CaseSnapshot:
    case_number: str          # ex: "3702/2024"
    status: str               # ex: "ATTESA DEPOSITO NOTE IN SOSTITUZIONE UDIENZA"
    last_historical_record: str   # última movimentação / last movement
    queue_position: str       # posição na fila / queue position
    last_check: str           # horário da consulta / consultation timestamp
    raw_timeline: list[str]   # todos os eventos / all timeline events


def fetch_case_snapshot(case_number: str, year: str, court_name: str = "L'Aquila Ordinary Court") -> CaseSnapshot:
    """
    PT: Acessa o site, preenche o formulário e retorna um CaseSnapshot
        com os dados atuais do processo. Aguarda até 60s para o
        Cloudflare Turnstile resolver automaticamente.

    EN: Accesses the site, fills in the form, and returns a CaseSnapshot
        with current case data. Waits up to 60s for Cloudflare Turnstile
        to resolve automatically.
    """
    url = "https://laviaitalia.com.br/processo-de-cidadania/consultar-processo"

    with sync_playwright() as p:
        # PT: Lançamos o Chromium em modo headless (sem janela visível).
        #     O argumento `--no-sandbox` é necessário em ambientes Linux CI.
        # EN: Launch Chromium in headless mode (no visible window).
        #     `--no-sandbox` is required in Linux CI environments.
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            # PT: Fingimos ser um Chrome real para reduzir detecção.
            # EN: Pretend to be a real Chrome to reduce detection.
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        logger.info("Navigating to %s", url)
        page.goto(url, wait_until="networkidle", timeout=60_000)

        # ---------------------------------------------------------------
        # PT: Preenche o campo "Número do Processo"
        # EN: Fill in the "Case Number" field
        # ---------------------------------------------------------------
        page.fill('input[placeholder*="Número"], input[name*="numero"], input[id*="numero"]', case_number)

        # PT: Preenche o campo "Ano"
        # EN: Fill in the "Year" field
        page.fill('input[placeholder*="Ano"], input[name*="ano"], input[id*="ano"]', year)

        # ---------------------------------------------------------------
        # PT: Seleciona o tribunal no dropdown.
        #     Primeiro abre o select customizado, depois filtra pelo nome.
        # EN: Select the court in the dropdown.
        #     First open the custom select, then filter by name.
        # ---------------------------------------------------------------
        # PT: Tenta clicar no select customizado (não é um <select> nativo)
        # EN: Try to click the custom select (not a native <select>)
        page.click('.select__control, [class*="select"][class*="control"], [aria-haspopup="listbox"]')
        time.sleep(0.5)

        # PT: Digita para filtrar as opções
        # EN: Type to filter options
        page.keyboard.type(court_name[:8])  # "L'Aquila"
        time.sleep(1)

        # PT: Clica na primeira opção que aparecer
        # EN: Click the first option that appears
        page.click('.select__option:first-child, [class*="option"]:first-child', timeout=5_000)

        # ---------------------------------------------------------------
        # PT: Aguarda o Turnstile resolver e clica em "Pesquisar Processo"
        # EN: Wait for Turnstile to resolve and click "Search Process"
        # ---------------------------------------------------------------
        logger.info("Waiting for Turnstile to resolve (up to 60s)…")
        # PT: O botão fica habilitado depois que o CAPTCHA resolve
        # EN: The button becomes enabled after CAPTCHA resolves
        page.wait_for_selector(
            'button:has-text("PESQUISAR"), button:has-text("SEARCH")',
            state="enabled",
            timeout=60_000,
        )
        page.click('button:has-text("PESQUISAR"), button:has-text("SEARCH")')

        # PT: Aguarda o painel de resultados aparecer
        # EN: Wait for the results panel to appear
        page.wait_for_selector('[class*="status"], [class*="processo"], h2, .card', timeout=30_000)
        time.sleep(2)  # pequena pausa para renderização / small rendering pause

        # ---------------------------------------------------------------
        # PT: Extrai os dados da página
        # EN: Extract data from the page
        # ---------------------------------------------------------------
        snapshot = _parse_page(page, case_number, year)

        browser.close()
        return snapshot


def _parse_page(page, case_number: str, year: str) -> CaseSnapshot:
    """
    PT: Lê o HTML da página de resultado e constrói um CaseSnapshot.
        Usa seletores amplos + regex para ser resiliente a mudanças no layout.

    EN: Reads the result page HTML and builds a CaseSnapshot.
        Uses broad selectors + regex to be resilient to layout changes.
    """
    content = page.content()

    def _text(selector: str, fallback: str = "N/A") -> str:
        try:
            el = page.query_selector(selector)
            return el.inner_text().strip() if el else fallback
        except Exception:
            return fallback

    # PT: Tenta múltiplos seletores para cada campo (o site pode mudar)
    # EN: Tries multiple selectors per field (site may change)
    status = (
        _text('[class*="status"]')
        or _text('h2')
        or _extract_regex(content, r"STATUS.*?([A-Z ]{10,})", fallback="N/A")
    )

    last_record = _text('[class*="historical"], [class*="last-record"]')
    queue_pos   = _text('[class*="queue"], [class*="posicao"]')
    last_check  = _text('[class*="last-check"], [class*="ultima"]')

    # PT: Extrai todos os eventos da timeline como lista de strings
    # EN: Extract all timeline events as a list of strings
    timeline_items = page.query_selector_all('[class*="timeline"] li, [class*="timeline"] > div')
    timeline = [el.inner_text().strip() for el in timeline_items if el.inner_text().strip()]

    return CaseSnapshot(
        case_number=f"{case_number}/{year}",
        status=status,
        last_historical_record=last_record,
        queue_position=queue_pos,
        last_check=last_check,
        raw_timeline=timeline,
    )


def _extract_regex(text: str, pattern: str, fallback: str = "N/A") -> str:
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else fallback

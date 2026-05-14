"""
state.py
========
PT: Gerencia o estado persistido do processo.
    Salva o último snapshot em JSON e detecta diferenças entre execuções.

EN: Manages the persisted case state.
    Saves the last snapshot as JSON and detects differences between runs.

Por que JSON?
Why JSON?
  PT: Simples, legível por humanos e versionável pelo Git.
      O histórico de mudanças fica visível nos commits do repositório.
  EN: Simple, human-readable, and Git-versionable.
      The change history is visible in the repository commits.
"""

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from scraper import CaseSnapshot

logger = logging.getLogger(__name__)

# PT: Caminho do arquivo de estado — fica na raiz do projeto
# EN: State file path — lives at the project root
STATE_FILE = Path("state.json")


def load_previous_snapshot() -> Optional[dict]:
    """
    PT: Carrega o snapshot anterior do arquivo JSON.
        Retorna None se o arquivo ainda não existir (primeira execução).

    EN: Loads the previous snapshot from the JSON file.
        Returns None if the file doesn't exist yet (first run).
    """
    if not STATE_FILE.exists():
        logger.info("No previous state found — this is the first run.")
        return None

    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_snapshot(snapshot: CaseSnapshot) -> None:
    """
    PT: Serializa o snapshot atual para JSON e grava no disco.
        O GitHub Actions fará commit desse arquivo após cada execução.

    EN: Serializes the current snapshot to JSON and writes to disk.
        GitHub Actions will commit this file after each run.
    """
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(asdict(snapshot), f, ensure_ascii=False, indent=2)
    logger.info("State saved to %s", STATE_FILE)


def detect_changes(previous: Optional[dict], current: CaseSnapshot) -> list[dict]:
    """
    PT: Compara o snapshot anterior com o atual e retorna uma lista
        de mudanças detectadas. Cada mudança é um dict com:
          - field: nome do campo que mudou
          - old:   valor anterior
          - new:   valor novo

    EN: Compares the previous snapshot with the current one and returns
        a list of detected changes. Each change is a dict with:
          - field: name of the changed field
          - old:   previous value
          - new:   new value
    """
    if previous is None:
        # PT: Primeira execução — não há "mudança", apenas registro inicial
        # EN: First run — no "change", just the initial record
        return []

    current_dict = asdict(current)
    changes = []

    # PT: Campos monitorados (excluímos last_check pois muda sempre)
    # EN: Monitored fields (we exclude last_check as it always changes)
    watched_fields = ["status", "last_historical_record", "queue_position", "raw_timeline"]

    for field in watched_fields:
        old_val = previous.get(field)
        new_val = current_dict.get(field)

        if old_val != new_val:
            changes.append({"field": field, "old": old_val, "new": new_val})
            logger.info("Change detected in '%s': %s → %s", field, old_val, new_val)

    return changes

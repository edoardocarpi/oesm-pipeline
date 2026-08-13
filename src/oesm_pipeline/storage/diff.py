"""
Confronto tra righe candidate (appena normalizzate) e righe già in Supabase.

Perché questo modulo esiste da solo: il trigger set_updated_at() su Postgres
aggiorna updated_at ad OGNI scrittura, anche se il valore non è cambiato. Il
monitor homelab-monitor usa MAX(updated_at) per capire da quanti giorni i
dati sono fermi. Se scrivessimo ogni riga ad ogni run (upsert "cieco"), il
monitor penserebbe sempre che i dati sono freschi anche quando la fonte non
ha pubblicato nulla di nuovo — un bug silenzioso, non un errore che si vede.
Per questo: si scrive una riga SOLO se il valore è nuovo o diverso da quello
già presente.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class DiffAction(Enum):
    INSERT = auto()   # non esiste ancora una riga per (indicator_code, year)
    UPDATE = auto()    # esiste ma il valore è cambiato
    SKIP = auto()      # esiste ed è identico: NON scrivere, per non toccare updated_at


@dataclass(frozen=True)
class DiffResult:
    action: DiffAction
    existing_id: int | None
    row: dict  # il record pronto per essere scritto (solo per INSERT/UPDATE)


# Campi che, se diversi, giustificano una scrittura. value_display è il
# confronto principale; gli altri intercettano correzioni metodologiche
# (es. cambio di unit_display) o editoriali (es. etichetta più leggibile)
# anche a valore invariato.
COMPARED_FIELDS = ("value_display", "unit_display", "conversion_note", "indicator_it")


def compute_diff(candidate_rows: list[dict], existing_rows: list[dict]) -> list[DiffResult]:
    existing_by_year = {row["year"]: row for row in existing_rows}
    results = []

    for candidate in candidate_rows:
        existing = existing_by_year.get(candidate["year"])

        if existing is None:
            results.append(DiffResult(DiffAction.INSERT, None, candidate))
            continue

        changed = any(
            _normalize_for_compare(existing.get(field)) != _normalize_for_compare(candidate.get(field))
            for field in COMPARED_FIELDS
        )
        if changed:
            results.append(DiffResult(DiffAction.UPDATE, existing["id"], candidate))
        else:
            results.append(DiffResult(DiffAction.SKIP, existing["id"], candidate))

    return results


def _normalize_for_compare(value) -> str | None:
    """Confronto robusto a differenze di tipo (es. '173.07' vs 173.07)
    che non sono un cambiamento di valore reale."""
    if value is None:
        return None
    return str(value)

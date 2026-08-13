"""
Lettura e validazione di config/indicators.yaml.

Qui vive la whitelist delle 7 categorie: uno slug diverso da questi non deve
mai arrivare a Supabase in silenzio (il documento di riferimento segnala che
il sito, in quel caso, non fa sparire l'indicatore ma perde l'etichetta di
navigazione corretta — un errore silenzioso che vogliamo intercettare qui).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_CATEGORIES = {
    "macroeconomia",
    "lavoro",
    "prezzi",
    "commercio",
    "finanza_pubblica",
    "turismo",
    "generale",
}


@dataclass(frozen=True)
class IndicatorDefinition:
    indicator_code: str
    indicator_it: str
    category: str
    source: str
    source_indicator: str
    eur_conversion: str
    unit_display: str
    status: str
    value_scale: float = 1.0  # es. 1_000_000 se la fonte pubblica in milioni


@dataclass(frozen=True)
class WeoVintage:
    release: str
    estimates_start_year: int


class ConfigError(ValueError):
    """Config non valida: categoria fuori whitelist, indicator_code duplicato, ecc."""


def load_indicators(path: str | Path) -> list[IndicatorDefinition]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    definitions = []
    seen_codes: set[str] = set()

    for entry in raw["indicators"]:
        if entry["category"] not in VALID_CATEGORIES:
            raise ConfigError(
                f"'{entry['indicator_code']}': categoria '{entry['category']}' non è "
                f"tra quelle valide {sorted(VALID_CATEGORIES)}. Controllare la tabella "
                f"'categorie' su Supabase prima di aggiungerne una nuova."
            )
        if entry["indicator_code"] in seen_codes:
            raise ConfigError(f"indicator_code duplicato in config: {entry['indicator_code']}")
        seen_codes.add(entry["indicator_code"])

        definitions.append(
            IndicatorDefinition(
                indicator_code=entry["indicator_code"],
                indicator_it=entry["indicator_it"],
                category=entry["category"],
                source=entry["source"],
                source_indicator=entry["source_indicator"],
                eur_conversion=entry["eur_conversion"],
                unit_display=entry["unit_display"],
                status=entry.get("status", "active"),
                value_scale=entry.get("value_scale", 1.0),
            )
        )
    return definitions


def load_weo_vintage(path: str | Path) -> WeoVintage:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    vintage = raw["weo_vintage"]
    return WeoVintage(release=vintage["release"], estimates_start_year=vintage["estimates_start_year"])

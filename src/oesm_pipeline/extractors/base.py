"""
Formato intermedio comune a tutti gli estrattori.

Ogni estrattore (World Bank, IMF, in futuro altri) restituisce una lista di
RawObservation — dati ancora grezzi, nella forma in cui li dà la fonte.
La normalizzazione (mapping su indicator_code, formattazione value_display,
conversione EUR) avviene sempre dopo, in un unico posto (normalize/), mai
dentro l'estrattore. Così ogni fonte nuova aggiunge solo un file qui dentro,
senza toccare il resto della pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RawObservation:
    """Un singolo punto dato così come arriva dalla fonte, non ancora normalizzato."""

    source_indicator: str      # codice usato dalla fonte originale (es. "NGDP_RPCH")
    source_name: str           # es. "World Bank", "International Monetary Fund"
    country_code: str          # ISO3, es. "SMR"
    year: int
    value: float | None        # None = nessun dato per quell'anno dalla fonte
    unit: str | None = None    # unità così come la esprime la fonte, se disponibile
    is_estimate: bool = False  # proiezione/stima dichiarata dalla fonte, non consuntivo


class Extractor(Protocol):
    """Contratto che ogni estrattore deve rispettare."""

    def fetch(self, source_indicator: str, country_code: str = "SMR") -> list[RawObservation]:
        """Recupera la serie storica completa per un indicatore e un paese."""
        ...

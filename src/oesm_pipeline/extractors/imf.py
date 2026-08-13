"""
Estrattore per la IMF DataMapper API.

Documentazione: https://www.imf.org/external/datamapper/api/help
Nessuna chiave richiesta. Endpoint: /api/v2/{indicatore}/{paese}

Nota sulle stime: questa API non marca i singoli punti dato come
"stima/proiezione" — quell'informazione esiste solo nell'appendice
statistica del World Economic Outlook (pubblicazione separata, PDF).
Per questo il confine stima/consuntivo è configurato a mano in
config/indicators.yaml (weo_vintage.estimates_start_year) e va
riverificato a ogni nuova uscita del WEO (aprile/ottobre). Vedi
METHODOLOGY.md per i dettagli.
"""

from __future__ import annotations

import httpx

from .base import RawObservation

BASE_URL = "https://www.imf.org/external/datamapper/api/v2"
TIMEOUT = 20.0


class IMFExtractor:
    def __init__(self, estimates_start_year: int, client: httpx.Client | None = None):
        # estimates_start_year: primo anno da marcare come proiezione, non
        # consuntivo — arriva dalla config, non è dedotto dall'API (vedi sopra).
        self.estimates_start_year = estimates_start_year
        self._client = client or httpx.Client(timeout=TIMEOUT)

    def fetch(self, source_indicator: str, country_code: str = "SMR") -> list[RawObservation]:
        url = f"{BASE_URL}/{source_indicator}/{country_code}"
        response = self._client.get(url)
        response.raise_for_status()
        payload = response.json()

        try:
            by_year = payload["values"][source_indicator][country_code]
        except KeyError:
            # Indicatore o paese senza dati pubblicati: nessuna riga, non un errore.
            return []

        observations = []
        for year_str, value in by_year.items():
            year = int(year_str)
            observations.append(
                RawObservation(
                    source_indicator=source_indicator,
                    source_name="International Monetary Fund",
                    country_code=country_code,
                    year=year,
                    value=float(value) if value is not None else None,
                    unit=None,  # la DataMapper API non restituisce l'unità nel payload dati
                    is_estimate=year >= self.estimates_start_year,
                )
            )
        return sorted(observations, key=lambda o: o.year)

    def close(self) -> None:
        self._client.close()

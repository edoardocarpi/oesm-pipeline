"""
Estrattore per la World Bank API.

Documentazione: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
Nessuna chiave richiesta. Endpoint: /v2/country/{paese}/indicator/{indicatore}
Risposta paginata: [metadata, [righe...]]; per una serie singola paese/indicatore
di solito una pagina basta, ma gestiamo comunque la paginazione per sicurezza.
"""

from __future__ import annotations

import httpx

from .base import RawObservation

BASE_URL = "https://api.worldbank.org/v2"
TIMEOUT = 20.0


class WorldBankExtractor:
    def __init__(self, client: httpx.Client | None = None):
        self._client = client or httpx.Client(timeout=TIMEOUT)

    def fetch(self, source_indicator: str, country_code: str = "SMR") -> list[RawObservation]:
        observations: list[RawObservation] = []
        page = 1
        while True:
            url = f"{BASE_URL}/country/{country_code}/indicator/{source_indicator}"
            params = {"format": "json", "per_page": 1000, "page": page}
            response = self._client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

            if not payload or not isinstance(payload, list) or len(payload) < 2:
                break  # indicatore inesistente o nessun dato

            metadata, rows = payload[0], payload[1]
            if not rows:
                break

            for row in rows:
                value = row.get("value")
                observations.append(
                    RawObservation(
                        source_indicator=source_indicator,
                        source_name="World Bank",
                        country_code=country_code,
                        year=int(row["date"]),
                        value=float(value) if value is not None else None,
                        unit=None,
                        is_estimate=False,  # il WB non pubblica proiezioni in questa API
                    )
                )

            if page >= metadata.get("pages", 1):
                break
            page += 1

        return sorted(observations, key=lambda o: o.year)

    def close(self) -> None:
        self._client.close()

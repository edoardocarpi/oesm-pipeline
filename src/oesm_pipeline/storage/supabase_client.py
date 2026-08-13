"""
Client minimale per Supabase via PostgREST diretto.

Niente SDK: PostgREST è già un'API REST completa (filtri, upsert via header
Prefer) e usare httpx direttamente rende esplicito e verificabile ogni
scrittura — coerente con l'impostazione "trasparente" del progetto, ed evita
una dipendenza in più senza un vantaggio concreto per questo caso d'uso.

Non passiamo mai `id` in scrittura (lo genera Postgres) e non passiamo mai
`updated_at` (lo gestisce il trigger set_updated_at()) — vedi documento di
riferimento della pipeline.
"""

from __future__ import annotations

import httpx


class SupabaseClient:
    def __init__(self, url: str, service_role_key: str, client: httpx.Client | None = None):
        self.rest_url = f"{url.rstrip('/')}/rest/v1"
        self._headers = {
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
        }
        self._client = client or httpx.Client(timeout=30.0)

    def get_existing_rows(self, indicator_code: str) -> list[dict]:
        """Righe già presenti per un indicator_code, per il confronto in diff.py."""
        response = self._client.get(
            f"{self.rest_url}/indicatori_dati",
            headers=self._headers,
            params={
                "indicator_code": f"eq.{indicator_code}",
                "select": "id,indicator_code,indicator_it,year,value_display,value_eur,"
                          "eur_rate_used,conversion_note,unit_display",
            },
        )
        response.raise_for_status()
        return response.json()

    def upsert_row(self, row: dict, existing_id: int | None) -> None:
        """Se existing_id è dato: UPDATE mirato su quella riga (mai passando id
        nel body). Altrimenti: INSERT di una riga nuova."""
        if existing_id is not None:
            response = self._client.patch(
                f"{self.rest_url}/indicatori_dati",
                headers=self._headers,
                params={"id": f"eq.{existing_id}"},
                json=row,
            )
        else:
            response = self._client.post(
                f"{self.rest_url}/indicatori_dati",
                headers={**self._headers, "Prefer": "return=minimal"},
                json=row,
            )
        response.raise_for_status()

    def delete_row(self, row_id: int) -> None:
        """Rimuove una riga per id — usato per ripulire anni di proiezione
        troppo lontani nel tempo, non più pubblicati (vedi MAX_PROJECTION_YEARS_AHEAD)."""
        response = self._client.delete(
            f"{self.rest_url}/indicatori_dati",
            headers=self._headers,
            params={"id": f"eq.{row_id}"},
        )
        response.raise_for_status()

    def close(self) -> None:
        self._client.close()

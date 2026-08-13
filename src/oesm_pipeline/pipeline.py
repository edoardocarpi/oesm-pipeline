from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from .extractors.base import Extractor, RawObservation
from .normalize import currency, formatting
from .normalize.mapping import IndicatorDefinition
from .storage.diff import DiffAction, compute_diff
from .storage.supabase_client import SupabaseClient

logger = logging.getLogger("oesm_pipeline")

# Quante proiezioni future pubblichiamo oltre l'anno corrente. Le previsioni
# dell'FMI arrivano fino a 5 anni avanti, ma per un microstato senza modello
# previsionale dedicato quegli anni lontani spesso ripetono lo stesso valore
# (l'abbiamo visto: GGR_G01_GDP_PT ripete 21.108956727209 dal 2027 al 2029) —
# proiezioni che è "sicuramente impossibile azzeccare" non aggiungono
# informazione, solo falsa precisione. Un solo anno oltre il corrente resta
# comunque utile e ragionevolmente affidabile.
MAX_PROJECTION_YEARS_AHEAD = 1


def max_allowed_year(today: date | None = None) -> int:
    today = today or date.today()
    return today.year + MAX_PROJECTION_YEARS_AHEAD


@dataclass
class RunReport:
    indicator_code: str
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    deleted: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def build_row(definition: IndicatorDefinition, obs: RawObservation, weo_release: str | None = None) -> dict:
    """Da un'osservazione grezza a un record pronto per Supabase,
    applicando scala, formattazione, conversione EUR e segnalazione delle proiezioni."""
    scaled_value = obs.value * definition.value_scale if obs.value is not None else None
    conversion = currency.convert(scaled_value, definition.eur_conversion, obs.year)

    # value_display deve mostrare il valore in EUR quando esiste una conversione
    # (altrimenti pubblicheremmo un numero in USD sotto un'unità dichiarata EUR).
    # Per gli indicatori needs_rate senza un tasso reale disponibile per quell'anno
    # (proiezioni future), meglio nessun valore che uno in una valuta sbagliata.
    if conversion.value_eur is not None:
        display_value = conversion.value_eur
    elif definition.eur_conversion == "needs_rate":
        display_value = None
    else:
        display_value = scaled_value

    notes = []
    if conversion.conversion_note:
        notes.append(conversion.conversion_note)
    if obs.is_estimate:
        # Frase leggibile con spazi: MAI una parola sola minuscola come "projection",
        # o il sito la tratta come codice tecnico interno e la nasconde (vedi
        # METHODOLOGY.md e il bug trovato nei dati dello script precedente).
        vintage = f", World Economic Outlook {weo_release}" if weo_release else ""
        notes.append(f"Proiezione FMI{vintage}, non dato consuntivo.")
    conversion_note = " ".join(notes) if notes else None

    row = {
        "indicator_code": definition.indicator_code,
        "indicator_it": definition.indicator_it,
        "category": definition.category,
        "source": definition.source,
        "source_code": definition.source_indicator,
        "country_code": obs.country_code,
        "country": "San Marino",
        "year": obs.year,
        "value_original": scaled_value,
        "value_display": formatting.format_value_display(display_value),
        "value_eur": conversion.value_eur,
        "unit_display": definition.unit_display,
        "eur_rate_used": conversion.eur_rate_used,
        "conversion_note": conversion_note,
    }
    return row


def run_indicator(
    definition: IndicatorDefinition,
    extractor: Extractor,
    supabase: SupabaseClient,
    *,
    dry_run: bool = False,
    weo_release: str | None = None,
) -> RunReport:
    report = RunReport(indicator_code=definition.indicator_code)
    logger.info("Estrazione %s (fonte: %s, codice %s)",
                definition.indicator_code, definition.source, definition.source_indicator)

    try:
        observations = extractor.fetch(definition.source_indicator)
    except Exception as exc:  # noqa: BLE001 - vogliamo loggare e continuare con gli altri indicatori
        report.errors.append(f"estrazione fallita: {exc}")
        logger.error("Estrazione fallita per %s: %s", definition.indicator_code, exc)
        return report

    cutoff = max_allowed_year()
    observations = [obs for obs in observations if obs.year <= cutoff]

    candidate_rows = [build_row(definition, obs, weo_release) for obs in observations]
    existing_rows_all = supabase.get_existing_rows(definition.indicator_code)

    # Righe già scritte in run precedenti per anni oltre il limite di proiezione
    # attuale (es. quando pubblicavamo fino al 2031): vanno rimosse, non solo
    # ignorate, altrimenti resterebbero orfane in tabella indefinitamente.
    rows_to_delete = [row for row in existing_rows_all if row["year"] > cutoff]
    existing_rows = [row for row in existing_rows_all if row["year"] <= cutoff]

    # Il World Bank restituisce una riga per OGNI anno dal 1960, anche quando
    # non ha il dato (value: null) — senza questo filtro finiremmo per inserire
    # centinaia di righe vuote e inutili per gli anni mai coperti dalla fonte.
    # Un anno senza dato E senza riga già esistente: semplicemente non si scrive,
    # "nessuna riga" equivale a "NULL" per il sito. Se invece la riga esiste già
    # (es. la fonte aveva un valore che ora è sparito per una revisione), la
    # lasciamo passare al diff, che potrà correttamente proporne l'aggiornamento.
    existing_years = {row["year"] for row in existing_rows}
    candidate_rows = [
        row for row in candidate_rows
        if row["value_display"] is not None or row["year"] in existing_years
    ]

    diffs = compute_diff(candidate_rows, existing_rows)

    for row in rows_to_delete:
        if dry_run:
            logger.info("[dry-run] DELETE %s anno=%s (oltre il limite di proiezione, %d)",
                        definition.indicator_code, row["year"], cutoff)
        else:
            try:
                supabase.delete_row(row["id"])
                report.deleted += 1
            except Exception as exc:  # noqa: BLE001
                report.errors.append(f"cancellazione anno {row['year']} fallita: {exc}")
                logger.error("Cancellazione fallita per %s anno %s: %s",
                             definition.indicator_code, row["year"], exc)

    for diff in diffs:
        if diff.action == DiffAction.SKIP:
            report.skipped += 1
            continue

        if dry_run:
            logger.info("[dry-run] %s %s anno=%s -> %s",
                        diff.action.name, definition.indicator_code,
                        diff.row["year"], diff.row["value_display"])
        else:
            try:
                supabase.upsert_row(diff.row, diff.existing_id)
            except Exception as exc:  # noqa: BLE001
                report.errors.append(f"scrittura anno {diff.row['year']} fallita: {exc}")
                logger.error("Scrittura fallita per %s anno %s: %s",
                             definition.indicator_code, diff.row["year"], exc)
                continue

        if diff.action == DiffAction.INSERT:
            report.inserted += 1
        elif diff.action == DiffAction.UPDATE:
            report.updated += 1

    logger.info(
        "%s: %d nuove, %d aggiornate, %d invariate, %d cancellate, %d errori",
        definition.indicator_code, report.inserted, report.updated,
        report.skipped, report.deleted, len(report.errors),
    )
    return report

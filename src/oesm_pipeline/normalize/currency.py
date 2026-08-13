"""
Conversione in EUR.

Regola generale (vedi METHODOLOGY.md): si preferisce sempre una serie già
denominata in EUR alla fonte (valuta locale per San Marino, dato che usa
l'euro) piuttosto che riconvertire un valore che la fonte stessa ha già
convertito da EUR a USD — quella doppia conversione introduce rumore ed è
metodologicamente più debole. La conversione con tasso BCE è quindi il
percorso di fallback, non quello preferito.

eur_conversion, da config/indicators.yaml:
  - "none": non è una cifra monetaria (percentuale, indice, conteggio) —
    value_eur = value_original così com'è
  - "already_eur": la fonte è già in EUR (es. serie in valuta locale per
    San Marino) — nessuna conversione, solo passaggio diretto
  - "needs_rate": la fonte è in USD, serve un tasso di cambio medio annuo
  - "not_applicable": PPP o simili — NON è una conversione di cambio,
    non forzare in value_eur (vedi IMF.PPPPC)
"""

from __future__ import annotations

from dataclasses import dataclass

# Tassi di cambio USD/EUR (dollari per un euro), media annua.
# Fonte: tassi di riferimento BCE / Federal Reserve (le due serie coincidono
# a meno di differenze marginali di arrotondamento, immateriali per un dato
# arrotondato a 2 decimali in EUR come facciamo qui).
#
# Copertura intenzionalmente limitata:
# - non prima del 1999 (l'euro non esisteva ancora)
# - non oltre l'ultimo anno solare concluso (LAST_COMPLETE_YEAR, da
#   aggiornare ogni gennaio quando l'anno precedente si chiude davvero)
# Per gli anni fuori da questo intervallo — proiezioni future incluse —
# non esiste un tasso medio annuo reale: NON ne inventiamo uno, si lascia
# la conversione assente piuttosto che pubblicare un numero costruito su
# un'ipotesi di cambio.
ECB_USD_PER_EUR_ANNUAL_AVERAGE = {
    1999: 1.0658, 2000: 0.9236, 2001: 0.8956, 2002: 0.9456, 2003: 1.1312,
    2004: 1.2439, 2005: 1.2441, 2006: 1.2556, 2007: 1.3705, 2008: 1.4708,
    2009: 1.3948, 2010: 1.3257, 2011: 1.3920, 2012: 1.2848, 2013: 1.3281,
    2014: 1.3285, 2015: 1.1095, 2016: 1.1069, 2017: 1.1297, 2018: 1.1810,
    2019: 1.1195, 2020: 1.1422, 2021: 1.1827, 2022: 1.0530, 2023: 1.0813,
    2024: 1.0817, 2025: 1.1306,
}
LAST_COMPLETE_YEAR = 2025


def ecb_annual_average_rate(year: int) -> float | None:
    if year < 1999 or year > LAST_COMPLETE_YEAR:
        return None
    return ECB_USD_PER_EUR_ANNUAL_AVERAGE.get(year)


@dataclass(frozen=True)
class ConversionResult:
    value_eur: float | None
    eur_rate_used: float | None
    conversion_note: str | None


def convert(
    value: float | None,
    mode: str,
    year: int,
    *,
    rate_lookup=None,
) -> ConversionResult:
    """rate_lookup: funzione opzionale (anno) -> tasso, iniettabile nei test
    al posto della tabella BCE reale."""

    if value is None:
        return ConversionResult(value_eur=None, eur_rate_used=None, conversion_note=None)

    if mode == "none":
        return ConversionResult(value_eur=value, eur_rate_used=None, conversion_note=None)

    if mode == "already_eur":
        return ConversionResult(
            value_eur=round(value, 2),
            eur_rate_used=None,
            conversion_note=(
                "Valore riportato dalla fonte direttamente in EUR "
                "(San Marino usa l'euro come valuta nazionale), nessuna conversione applicata."
            ),
        )

    if mode == "not_applicable":
        # PPP o simili: non è money-in-a-currency, non scriviamo value_eur.
        return ConversionResult(value_eur=None, eur_rate_used=None, conversion_note=None)

    if mode == "needs_rate":
        lookup = rate_lookup or ecb_annual_average_rate
        rate = lookup(year)
        if rate is None:
            return ConversionResult(
                value_eur=None,
                eur_rate_used=None,
                conversion_note=(
                    "Conversione in EUR non disponibile per questo anno: nessun tasso di "
                    "cambio medio annuo definitivo esistente (anno di proiezione non ancora "
                    "trascorso, o precedente all'introduzione dell'euro nel 1999)."
                ),
            )
        return ConversionResult(
            value_eur=round(value / rate, 2),
            eur_rate_used=rate,
            conversion_note=(
                f"Convertito da USD a EUR con il tasso di cambio di riferimento medio annuo "
                f"BCE per il {year} ({rate} USD per 1 EUR)."
            ),
        )

    raise ValueError(f"eur_conversion sconosciuto in config: {mode!r}")

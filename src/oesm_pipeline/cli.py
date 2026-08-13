from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .extractors.imf import IMFExtractor
from .extractors.worldbank import WorldBankExtractor
from .normalize.mapping import load_indicators, load_weo_vintage
from .pipeline import run_indicator
from .storage.supabase_client import SupabaseClient

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "indicators.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline dati economici OESM.net")
    parser.add_argument(
        "--indicator", metavar="CODE",
        help="Lancia solo su un indicator_code (es. IMF.PCPIPCH). Default: tutti gli 'active'.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Estrae e calcola il diff ma non scrive su Supabase — solo log.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Log a livello DEBUG.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    load_dotenv()
    supabase_url = os.environ.get("SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        # Servono anche in --dry-run: il diff si calcola leggendo lo stato reale
        # su Supabase, --dry-run salta solo la scrittura, non la lettura.
        sys.exit(
            "SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY devono essere impostate "
            "(vedi .env.example)."
        )

    definitions = load_indicators(CONFIG_PATH)
    weo_vintage = load_weo_vintage(CONFIG_PATH)

    if args.indicator:
        definitions = [d for d in definitions if d.indicator_code == args.indicator]
        if not definitions:
            sys.exit(f"Nessun indicator_code '{args.indicator}' in config/indicators.yaml")
    else:
        definitions = [d for d in definitions if d.status == "active"]

    imf_extractor = IMFExtractor(estimates_start_year=weo_vintage.estimates_start_year)
    wb_extractor = WorldBankExtractor()
    supabase = SupabaseClient(supabase_url, service_role_key)

    extractors_by_source = {
        "International Monetary Fund": imf_extractor,
        "World Bank": wb_extractor,
    }

    reports = []
    for definition in definitions:
        extractor = extractors_by_source.get(definition.source)
        if extractor is None:
            logging.error("Nessun estrattore registrato per la fonte '%s'", definition.source)
            continue
        report = run_indicator(
            definition, extractor, supabase,
            dry_run=args.dry_run, weo_release=weo_vintage.release,
        )
        reports.append(report)

    imf_extractor.close()
    wb_extractor.close()
    supabase.close()

    total_errors = sum(len(r.errors) for r in reports)
    if total_errors:
        sys.exit(f"Completato con {total_errors} errori — vedi log sopra.")


if __name__ == "__main__":
    main()

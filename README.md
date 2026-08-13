# oesm-pipeline

Pipeline di estrazione dati economici per [OESM.net](https://oesm.net), l'Osservatorio
Economico di San Marino. Scrive nella tabella `indicatori_dati` su Supabase, condivisa
con il CMS locale e il sito pubblico.

Per il contesto metodologico completo (fonti, criterio EUR, gestione stime/proiezioni)
vedi [`METHODOLOGY.md`](./METHODOLOGY.md).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # poi compila SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY
```

## Uso

```bash
# Un giro di prova, senza scrivere nulla: mostra solo cosa verrebbe scritto
oesm-pipeline --dry-run

# Un solo indicatore, utile per validare una fonte nuova prima di allargare
oesm-pipeline --indicator IMF.PCPIPCH --dry-run
oesm-pipeline --indicator IMF.PCPIPCH

# Tutti gli indicatori attivi in config/indicators.yaml
oesm-pipeline
```

## Test

```bash
pytest -v
```

I test degli estrattori usano risposte fedeli a quelle reali di IMF/World Bank,
salvate in `tests/fixtures/`: nessuna chiamata di rete durante i test.

## Aggiungere un indicatore

1. Verificare il codice presso la fonte (IMF DataMapper o World Bank API).
2. Aggiungere una voce in `config/indicators.yaml`: categoria, indicator_code
   definitivo (**stabile per sempre una volta pubblicato**), regola di conversione EUR.
3. `oesm-pipeline --indicator <CODE> --dry-run` per validare prima di scrivere.
4. Verificare su CMS locale → Archivio e sul sito pubblico `/dati/[code]`.

## Cosa questa pipeline NON fa

Le fonti sammarinesi (statistica.sm, BCSM) non sono automatizzate in scrittura:
solo un watcher che segnala e scarica nuovi bollettini PDF (vedi
`extractors/watchers/`), mai una scrittura diretta su Supabase. La scelta è
deliberata, vedi METHODOLOGY.md.

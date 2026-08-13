# oesm-pipeline

Scarica dati economici su San Marino da World Bank e Fondo Monetario Internazionale, li pulisce e li pubblica su [OESM.net](https://oesm.net), l'Osservatorio Economico di San Marino.

Per capire come vengono trattati i dati (fonti, conversione in euro, proiezioni), vedi [METHODOLOGY.md](./METHODOLOGY.md).

## Installazione

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Apri `.env` e inserisci l'URL del progetto Supabase e la service role key.

## Uso

```bash
# Prova senza scrivere nulla
oesm-pipeline --dry-run

# Un solo indicatore
oesm-pipeline --indicator IMF.PCPIPCH

# Tutti gli indicatori attivi
oesm-pipeline
```

## Test

```bash
pytest -v
```

## Aggiungere un indicatore

Aggiungi una voce in `config/indicators.yaml` (categoria, codice della fonte, regola di conversione), poi valida con `--dry-run` prima di scrivere per davvero. Una volta pubblicato, il codice dell'indicatore non va più cambiato: diventa parte dell'indirizzo della sua pagina.

## Cosa non fa

Le fonti statistiche sammarinesi pubblicano solo bollettini in PDF, non un formato leggibile automaticamente. Per queste fonti la pipeline si limita a segnalare quando esce un nuovo bollettino: i dati vengono inseriti a mano, per evitare errori di lettura.

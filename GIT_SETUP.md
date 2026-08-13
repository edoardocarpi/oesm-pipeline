# Pubblicare questo repo su GitHub

Questa cartella è pronta così com'è: `.gitignore` esclude già `.env`, le
cartelle generate (`__pycache__`, `.pytest_cache`, `data/downloads`, `logs`)
e l'ambiente virtuale. Nessun segreto è presente nei file.

## 1. Crea il repository vuoto su GitHub

Vai su https://github.com/new, scegli un nome (es. `oesm-pipeline`), **non**
selezionare "Initialize with README" (ce l'hai già qui), crealo.

## 2. Inizializza git in locale e collega il repo remoto

Dalla cartella `oesm-pipeline/` (questa stessa cartella):

```bash
git init
git add .
git commit -m "Prima versione della pipeline: estrattori WB/IMF, normalizzazione, diff, conversione EUR"
git branch -M main
git remote add origin https://github.com/<tuo-utente>/oesm-pipeline.git
git push -u origin main
```

Sostituisci `<tuo-utente>` con il tuo username GitHub e il nome scelto al
punto 1, se diverso da `oesm-pipeline`.

## 3. Verifica che .env non sia mai finito nel repo

Prima del primo push, un controllo di sicurezza:

```bash
git status
```

Non deve comparire `.env` tra i file tracciati, solo `.env.example`. Se per
errore `.env` compare, **non fare commit**: aggiungilo (o verifica che sia
già) in `.gitignore`, poi ripeti `git status` per confermare che sparisca
dall'elenco.

## 4. Ai push successivi

Una volta impostato, per ogni modifica futura basta:

```bash
git add .
git commit -m "descrizione della modifica"
git push
```

## Nota su questa consegna

`config/indicators.yaml` è il file che cambierà più spesso (nuovi
indicatori, etichette corrette, nuove voci in `indicatori_confronti` lato
Supabase). `pipeline.py`, `currency.py` e `diff.py` sono i moduli più
delicati: se in futuro li modifichi, rilancia sempre `pytest -v` prima di
fare commit.

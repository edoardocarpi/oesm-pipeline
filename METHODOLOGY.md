# Metodologia

Questo documento spiega, per chi consulta o cita i dati di OESM.net, da dove
vengono i numeri e come vengono trattati prima della pubblicazione. La lista
completa e sempre aggiornata degli indicatori è in
[`config/indicators.yaml`](./config/indicators.yaml).

## Fonti

Due fonti internazionali, automatizzate via API ufficiali:

- **International Monetary Fund**: World Economic Outlook (WEO), via
  [IMF DataMapper API](https://www.imf.org/external/datamapper/api/help).
  Fonte primaria per gli indicatori più recenti: l'FMI segue San Marino con
  consultazioni dirette (Articolo IV), quindi pubblica dati più aggiornati
  del World Bank per lo stesso paese.
- **World Bank**: World Development Indicators, via
  [World Bank API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392).
  Usato dove copre indicatori che l'IMF non traccia con lo stesso dettaglio
  per un microstato (commercio estero, popolazione, turismo), o come serie
  storica più lunga a fianco di un indicatore IMF equivalente.

Fonti sammarinesi ufficiali (Ufficio Informatica Tecnologia Dati e Statistica /
statistica.sm, Banca Centrale di San Marino) non sono al momento estratte in
automatico: pubblicano solo bollettini PDF, non un'API o un dataset
scaricabile in formato strutturato. Un watcher segnala e scarica i nuovi
bollettini man mano che escono, ma l'inserimento dei dati resta manuale, per
evitare che un errore di lettura di una tabella PDF finisca online senza
controllo.

## Conversione in EUR

Regola generale: **si preferisce sempre una serie già denominata in EUR alla
fonte**, piuttosto che convertire un valore che la fonte stessa ha già
convertito in un'altra valuta (tipicamente USD). Riconvertire un dato che è
già passato una volta da EUR a USD introduce una doppia conversione ed è
metodologicamente più debole. Per questo, quando esiste, si usa sempre la
serie in valuta locale (San Marino ha l'euro come valuta nazionale).

Esempio concreto: `NY.GDP.MKTP.CD` (PIL) mantiene il codice storico del World
Bank per "PIL, dollari correnti": non può essere rinominato, l'URL pubblico
`/dati/NY.GDP.MKTP.CD` è già in uso, ma la pipeline estrae la serie
`NY.GDP.MKTP.CN` (valuta locale, EUR) e la scrive sotto quel codice. È una
scelta editoriale deliberata: il nome del codice non descrive più la valuta
reale del dato pubblicato.

Quando una fonte pubblica solo in USD e non esiste una serie in valuta
locale (es. `IMF.NGDPD`, `IMF.NGDPDPC`, `IMF.BCA`), la pipeline converte con
il tasso di cambio di riferimento medio annuo BCE. La conversione copre solo
gli anni per cui esiste un tasso medio annuo realmente concluso, dal 1999
(introduzione dell'euro) fino all'ultimo anno solare completato. Per gli
anni fuori da questo intervallo (proiezioni non ancora trascorse, o
precedenti al 1999) non pubblichiamo un `value_eur`/`value_display`: non
esiste un tasso reale da usare, e inventarne uno sarebbe metodologicamente
scorretto. Fonte e tasso usato sono sempre documentati nel campo nota del
dato pubblicato.

Gli indicatori in **PPP** (es. PIL pro capite a parità di potere d'acquisto)
non vengono trattati come una conversione di cambio: PPP è un concetto
diverso, un tasso di cambio reale non si applica.

## Dati consuntivi vs proiezioni

Il World Economic Outlook dell'FMI include proiezioni fino a diversi anni
nel futuro. L'API IMF DataMapper non marca esplicitamente, punto per punto,
quali anni sono consuntivi e quali proiezioni: quell'informazione esiste
solo nell'appendice statistica della pubblicazione WEO (PDF), rilasciata
due volte l'anno (aprile e ottobre).

Per questo l'anno di cutoff (`weo_vintage.estimates_start_year` in
`config/indicators.yaml`) è impostato a mano ad ogni nuova uscita del WEO,
leggendo l'appendice statistica ufficiale. Vintage corrente: **{{ vedi
config/indicators.yaml, campo weo_vintage.release }}**.

**Quanto lontano pubblichiamo le proiezioni.** L'FMI proietta fino a 5 anni
avanti, ma per un microstato senza un modello previsionale dedicato gli anni
più lontani spesso ripetono lo stesso valore anno su anno, proiezioni che è
sicuramente impossibile azzeccare con quella precisione, e che aggiungono
falsa precisione più che informazione utile. Per questo pubblichiamo le
proiezioni solo fino a un anno oltre quello corrente, non oltre: è una
scelta editoriale deliberata, non un limite della fonte. Le righe per anni
più lontani, se presenti da versioni precedenti della pipeline, vengono
rimosse automaticamente ad ogni esecuzione.

## Aggiornamento dei dati e "freschezza"

La pipeline scrive una riga solo quando il valore è nuovo o diverso da
quello già pubblicato, non ad ogni esecuzione. La data di ultimo
aggiornamento mostrata sul sito riflette quindi l'ultima volta che la fonte
ha effettivamente pubblicato un valore nuovo, non l'ultima volta che la
pipeline è stata eseguita.

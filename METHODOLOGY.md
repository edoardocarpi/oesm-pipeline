# Metodologia

Questo documento spiega da dove vengono i numeri pubblicati su OESM.net e come vengono trattati prima di essere pubblicati.

## Fonti

I dati arrivano da due fonti internazionali, aggiornate tramite le loro API pubbliche:

- **Fondo Monetario Internazionale**, World Economic Outlook. È la fonte principale per gli indicatori più recenti: l'FMI segue San Marino con consultazioni dirette, quindi pubblica dati più aggiornati del World Bank.
- **World Bank**, World Development Indicators. Usato dove copre indicatori che l'FMI non traccia (commercio estero, popolazione, turismo), o insieme a un indicatore FMI equivalente quando le due fonti divergono e vale la pena mostrarle entrambe.

Le fonti statistiche sammarinesi pubblicano solo bollettini in PDF, non un formato leggibile automaticamente: per queste fonti i dati vengono inseriti a mano dopo ogni nuova pubblicazione, non dalla pipeline.

## Conversione in euro

Quando una fonte pubblica già un dato in euro, lo usiamo così com'è. Quando pubblica solo in dollari, lo convertiamo con il tasso di cambio medio annuo della Banca Centrale Europea relativo a quell'anno.

Questa conversione copre solo gli anni conclusi dal 1999 (nascita dell'euro) in poi. Per gli anni futuri, o precedenti al 1999, non pubblichiamo un valore in euro: non esiste un tasso di cambio reale per quegli anni, quindi non ne calcoliamo uno.

I valori espressi in parità di potere d'acquisto (PPP) non vengono convertiti: non sono legati a un tasso di cambio.

## Proiezioni

Il Fondo Monetario Internazionale pubblica anche proiezioni per gli anni futuri, insieme ai dati consuntivi. Mostriamo queste proiezioni solo per l'anno corrente e il successivo. Per un'economia piccola come San Marino, le proiezioni più lontane nel tempo tendono a ripetere lo stesso numero anno dopo anno: non aggiungono informazione utile, quindi non le pubblichiamo.

Quando un valore è una proiezione e non un dato consuntivo, la pagina dell'indicatore lo segnala.

## Aggiornamento dei dati

Scriviamo un valore solo quando cambia rispetto a quello già pubblicato, non ogni volta che la pipeline gira. La data di ultimo aggiornamento di un dato riflette quindi l'ultima volta che la fonte ha davvero pubblicato qualcosa di nuovo.

## Revisioni

Le fonti possono rivedere i propri dati storici nel tempo. Se un valore che avevi consultato in passato oggi risulta leggermente diverso, è quasi sempre per questo motivo.

-- Tabella per i confronti a due colonne/due linee tra fonti diverse sullo
-- stesso concetto (World Bank vs FMI). Popolamento manuale, non dalla
-- pipeline — stesso principio della tabella categorie.
--
-- Niente FOREIGN KEY verso indicatori_dati(indicator_code): quella colonna
-- non è univoca (si ripete una volta per ogni anno), quindi non può essere
-- il bersaglio di una FK. La coerenza si verifica a mano prima di inserire
-- (vedi query di controllo più sotto), non imposta dal database.

CREATE TABLE IF NOT EXISTS indicatori_confronti (
  gruppo_slug text NOT NULL,        -- stabile, diventa l'URL della pagina di confronto
  indicator_code text NOT NULL,
  ordine smallint DEFAULT 0,        -- quale linea/colonna viene prima
  PRIMARY KEY (gruppo_slug, indicator_code)
);

-- RLS: stessa policy di lettura pubblica delle altre tabelle consultate dal sito
ALTER TABLE indicatori_confronti ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon puo leggere indicatori_confronti"
  ON indicatori_confronti FOR SELECT
  TO anon
  USING (true);

-- Le sei coppie identificate in questa conversazione
INSERT INTO indicatori_confronti (gruppo_slug, indicator_code, ordine) VALUES
  ('crescita-pil-reale',    'NY.GDP.MKTP.KD.ZG', 1),
  ('crescita-pil-reale',    'IMF.NGDP_RPCH',     2),

  ('inflazione-ipc',        'FP.CPI.TOTL.ZG',    1),
  ('inflazione-ipc',        'IMF.PCPIPCH',       2),

  ('pil-livello',           'NY.GDP.MKTP.CD',    1),
  ('pil-livello',           'IMF.NGDPD',         2),

  ('pil-pro-capite',        'NY.GDP.PCAP.CD',    1),
  ('pil-pro-capite',        'IMF.NGDPDPC',       2),

  ('spesa-pubblica',        'GC.XPN.TOTL.GD.ZS', 1),
  ('spesa-pubblica',        'IMF.G_X_G01_GDP_PT', 2),

  ('popolazione',           'SP.POP.TOTL',       1),
  ('popolazione',           'IMF.LP',            2)
ON CONFLICT (gruppo_slug, indicator_code) DO NOTHING;

-- Verifica 1: ogni gruppo deve avere esattamente 2 righe
SELECT gruppo_slug, COUNT(*) AS n_fonti
FROM indicatori_confronti
GROUP BY gruppo_slug
ORDER BY gruppo_slug;

-- Verifica 2: nessun indicator_code "orfano" (senza corrispondenza reale
-- in indicatori_dati) — sostituisce il controllo che una FK avrebbe fatto
-- automaticamente, fatto qui a mano
SELECT DISTINCT c.indicator_code
FROM indicatori_confronti c
LEFT JOIN indicatori_dati d ON d.indicator_code = c.indicator_code
WHERE d.indicator_code IS NULL;

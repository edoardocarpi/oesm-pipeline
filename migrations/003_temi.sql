-- Sostituisce indicatori_confronti con uno schema pensato per "una pagina
-- per concetto", non "una pagina per indicator_code". temi = i concetti con
-- più di una fonte (slug stabile, quello che diventa l'URL pubblico);
-- temi_fonti = quali indicator_code appartengono a quel tema, in che ordine.
--
-- Gli indicatori a fonte singola (la maggioranza) non compaiono qui affatto:
-- restano pagine normali su /dati/[indicator_code], come sempre.

DROP TABLE IF EXISTS indicatori_confronti;

CREATE TABLE IF NOT EXISTS temi (
  slug text PRIMARY KEY,       -- es. 'pil', 'crescita-pil' — diventa l'URL /dati/[slug]
  titolo text NOT NULL,        -- es. 'PIL a prezzi correnti'
  categoria text NOT NULL      -- deve coincidere con uno slug della tabella categorie
);

CREATE TABLE IF NOT EXISTS temi_fonti (
  tema_slug text NOT NULL REFERENCES temi(slug),
  indicator_code text NOT NULL,  -- niente FK verso indicatori_dati: quella colonna
                                  -- non è univoca (una riga per anno), vedi verifica sotto
  ordine smallint DEFAULT 0,     -- quale fonte viene mostrata/elencata per prima
  PRIMARY KEY (tema_slug, indicator_code)
);

ALTER TABLE temi ENABLE ROW LEVEL SECURITY;
ALTER TABLE temi_fonti ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon puo leggere temi"
  ON temi FOR SELECT TO anon USING (true);

CREATE POLICY "anon puo leggere temi_fonti"
  ON temi_fonti FOR SELECT TO anon USING (true);

-- I sei concetti con più di una fonte, con slug neutri (niente gergo tecnico,
-- niente "-san-marino" ripetuto — il tag <title> del sito lo aggiunge già
-- automaticamente su ogni pagina, vedi app/layout.jsx)
INSERT INTO temi (slug, titolo, categoria) VALUES
  ('pil',              'PIL a prezzi correnti',      'macroeconomia'),
  ('crescita-pil',      'Crescita del PIL reale',     'macroeconomia'),
  ('pil-pro-capite',    'PIL pro capite',             'macroeconomia'),
  ('inflazione',        'Inflazione',                 'prezzi'),
  ('spesa-pubblica',    'Spesa pubblica',             'finanza_pubblica'),
  ('popolazione',       'Popolazione',                'generale')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO temi_fonti (tema_slug, indicator_code, ordine) VALUES
  ('pil',              'NY.GDP.MKTP.CD',     1),
  ('pil',              'IMF.NGDPD',          2),

  ('crescita-pil',      'NY.GDP.MKTP.KD.ZG',  1),
  ('crescita-pil',      'IMF.NGDP_RPCH',      2),

  ('pil-pro-capite',    'NY.GDP.PCAP.CD',     1),
  ('pil-pro-capite',    'IMF.NGDPDPC',        2),

  ('inflazione',        'FP.CPI.TOTL.ZG',     1),
  ('inflazione',        'IMF.PCPIPCH',        2),

  ('spesa-pubblica',    'GC.XPN.TOTL.GD.ZS',  1),
  ('spesa-pubblica',    'IMF.G_X_G01_GDP_PT', 2),

  ('popolazione',       'SP.POP.TOTL',        1),
  ('popolazione',       'IMF.LP',             2)
ON CONFLICT (tema_slug, indicator_code) DO NOTHING;

-- Verifica 1: ogni tema deve avere esattamente 2 fonti
SELECT tema_slug, COUNT(*) AS n_fonti
FROM temi_fonti
GROUP BY tema_slug
ORDER BY tema_slug;

-- Verifica 2: nessun indicator_code orfano (senza corrispondenza reale
-- in indicatori_dati) — sostituisce il controllo che una FK avrebbe fatto
SELECT DISTINCT t.indicator_code
FROM temi_fonti t
LEFT JOIN indicatori_dati d ON d.indicator_code = t.indicator_code
WHERE d.indicator_code IS NULL;

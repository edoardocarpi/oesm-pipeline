from oesm_pipeline.extractors.base import RawObservation
from oesm_pipeline.normalize.formatting import is_technical_code
from oesm_pipeline.normalize.mapping import IndicatorDefinition
from oesm_pipeline.pipeline import build_row, run_indicator

DEFINITION = IndicatorDefinition(
    indicator_code="IMF.PCPIPCH",
    indicator_it="Inflazione IPC % (FMI)",
    category="prezzi",
    source="International Monetary Fund",
    source_indicator="PCPIPCH",
    eur_conversion="none",
    unit_display="%",
    status="active",
)


def test_estimate_is_flagged_in_conversion_note_with_readable_sentence():
    obs = RawObservation(
        source_indicator="PCPIPCH", source_name="International Monetary Fund",
        country_code="SMR", year=2027, value=2.6, is_estimate=True,
    )

    row = build_row(DEFINITION, obs, weo_release="2026-04")

    assert row["conversion_note"] is not None
    assert "proiezione" in row["conversion_note"].lower()
    # Non deve MAI ridursi al bug trovato nei dati reali: una singola parola
    # minuscola senza spazi, che il sito nasconde trattandola come codice tecnico.
    assert not is_technical_code(row["conversion_note"])


def test_actual_value_has_no_projection_note():
    obs = RawObservation(
        source_indicator="PCPIPCH", source_name="International Monetary Fund",
        country_code="SMR", year=2024, value=1.2, is_estimate=False,
    )

    row = build_row(DEFINITION, obs, weo_release="2026-04")

    assert row["conversion_note"] is None


def test_missing_value_still_produces_a_row_with_null_display():
    obs = RawObservation(
        source_indicator="PCPIPCH", source_name="International Monetary Fund",
        country_code="SMR", year=2001, value=None, is_estimate=False,
    )

    row = build_row(DEFINITION, obs)

    assert row["value_display"] is None  # vero NULL, non stringa "null"


def test_unit_display_always_comes_from_config_never_left_empty():
    # Bug reale trovato in produzione: nessuna delle due API (WB, IMF) restituisce
    # l'unità nel payload dati — se non la si prende dalla config, le righe INSERT
    # nuove finiscono con unit_display NULL (le UPDATE invece la ereditano dal
    # valore già presente, per questo il bug non si vedeva su tutte le righe).
    obs = RawObservation(
        source_indicator="PCPIPCH", source_name="International Monetary Fund",
        country_code="SMR", year=2024, value=1.2, is_estimate=False,
    )

    row = build_row(DEFINITION, obs)

    assert row["unit_display"] == "%"


def test_value_scale_applied_before_formatting():
    # IMF.LP arriva in milioni di persone ("0.035"), va scalato in abitanti
    # per essere confrontabile con la serie World Bank equivalente (SP.POP.TOTL).
    definition = IndicatorDefinition(
        indicator_code="IMF.LP", indicator_it="Popolazione (milioni) — FMI",
        category="generale", source="International Monetary Fund",
        source_indicator="LP", eur_conversion="none", unit_display="abitanti",
        status="active", value_scale=1_000_000,
    )
    obs = RawObservation(
        source_indicator="LP", source_name="International Monetary Fund",
        country_code="SMR", year=2024, value=0.035, is_estimate=False,
    )

    row = build_row(definition, obs)

    assert row["value_display"] == "35000.0"


def test_value_scale_default_is_one_when_not_specified():
    obs = RawObservation(
        source_indicator="PCPIPCH", source_name="International Monetary Fund",
        country_code="SMR", year=2024, value=1.2, is_estimate=False,
    )

    row = build_row(DEFINITION, obs)  # DEFINITION non specifica value_scale

    assert row["value_display"] == "1.2"


NGDPD_DEFINITION = IndicatorDefinition(
    indicator_code="IMF.NGDPD", indicator_it="PIL a prezzi correnti — FMI",
    category="macroeconomia", source="International Monetary Fund",
    source_indicator="NGDPD", eur_conversion="needs_rate", unit_display="EUR",
    status="active", value_scale=1_000_000_000,
)


def test_value_display_shows_eur_not_raw_usd_when_conversion_available():
    # Bug reale trovato prima di aggiungere gli indicatori needs_rate: value_display
    # mostrava sempre il valore grezzo (USD), non quello convertito — avrebbe
    # pubblicato cifre in dollari sotto un'etichetta "EUR".
    obs = RawObservation(
        source_indicator="NGDPD", source_name="International Monetary Fund",
        country_code="SMR", year=2025, value=2.823, is_estimate=False,  # miliardi di USD
    )

    row = build_row(NGDPD_DEFINITION, obs)

    raw_usd = 2.823 * 1_000_000_000
    assert row["value_original"] == raw_usd  # il grezzo resta in USD, per trasparenza
    assert row["value_display"] != str(raw_usd)  # ma il display NON è il numero in USD
    assert float(row["value_display"]) == round(raw_usd / 1.1306, 2)


def test_value_display_empty_for_needs_rate_without_a_real_rate():
    # Anno di proiezione (2028): nessun tasso reale, quindi nessun value_display —
    # meglio nessun dato che un numero in EUR costruito su un cambio inventato.
    obs = RawObservation(
        source_indicator="NGDPD", source_name="International Monetary Fund",
        country_code="SMR", year=2028, value=3.0, is_estimate=True,
    )

    row = build_row(NGDPD_DEFINITION, obs)

    assert row["value_display"] is None
    assert row["value_eur"] is None


class _StubExtractor:
    def __init__(self, observations):
        self._observations = observations

    def fetch(self, source_indicator, country_code="SMR"):
        return self._observations


class _StubSupabase:
    def __init__(self, existing_rows):
        self._existing_rows = existing_rows
        self.written_rows = []
        self.deleted_ids = []

    def get_existing_rows(self, indicator_code):
        return self._existing_rows

    def upsert_row(self, row, existing_id):
        self.written_rows.append(row)

    def delete_row(self, row_id):
        self.deleted_ids.append(row_id)


def test_run_indicator_skips_empty_years_with_no_existing_row():
    # Bug reale trovato durante un run completo: il World Bank restituisce una
    # riga per OGNI anno dal 1960, anche senza dato (value: null). Senza questo
    # filtro la pipeline scriverebbe centinaia di righe vuote e inutili per gli
    # anni mai coperti dalla fonte.
    observations = [
        RawObservation(source_indicator="X", source_name="World Bank",
                        country_code="SMR", year=1960, value=None, is_estimate=False),
        RawObservation(source_indicator="X", source_name="World Bank",
                        country_code="SMR", year=2024, value=1.2, is_estimate=False),
    ]
    extractor = _StubExtractor(observations)
    supabase = _StubSupabase(existing_rows=[])

    report = run_indicator(DEFINITION, extractor, supabase, dry_run=False)

    assert report.inserted == 1  # solo il 2024, non il 1960 vuoto
    assert len(supabase.written_rows) == 1
    assert supabase.written_rows[0]["year"] == 2024


def test_run_indicator_keeps_empty_year_if_a_row_already_exists():
    # Se la riga esiste già (es. la fonte aveva un valore ora sparito per una
    # revisione), va comunque valutata dal diff — non ignorata a priori.
    observations = [
        RawObservation(source_indicator="X", source_name="World Bank",
                        country_code="SMR", year=2020, value=None, is_estimate=False),
    ]
    extractor = _StubExtractor(observations)
    existing = [{"id": 7, "year": 2020, "value_display": "5.0", "unit_display": "%",
                 "conversion_note": None, "indicator_it": DEFINITION.indicator_it}]
    supabase = _StubSupabase(existing_rows=existing)

    report = run_indicator(DEFINITION, extractor, supabase, dry_run=False)

    assert report.updated == 1  # il valore è passato da 5.0 a NULL: aggiornamento legittimo


def test_max_allowed_year_is_one_year_beyond_today():
    from datetime import date
    from oesm_pipeline.pipeline import max_allowed_year

    assert max_allowed_year(today=date(2026, 8, 12)) == 2027
    assert max_allowed_year(today=date(2027, 1, 3)) == 2028


def test_run_indicator_excludes_observations_beyond_projection_cutoff():
    # Proiezioni troppo lontane (oltre un anno dal presente) non vengono
    # nemmeno candidate alla scrittura: "sicuramente impossibili da azzeccare".
    observations = [
        RawObservation(source_indicator="X", source_name="International Monetary Fund",
                        country_code="SMR", year=2027, value=1.3, is_estimate=True),
        RawObservation(source_indicator="X", source_name="International Monetary Fund",
                        country_code="SMR", year=2031, value=1.3, is_estimate=True),
    ]
    extractor = _StubExtractor(observations)
    supabase = _StubSupabase(existing_rows=[])

    import oesm_pipeline.pipeline as pipeline_module
    original = pipeline_module.max_allowed_year
    pipeline_module.max_allowed_year = lambda today=None: 2027
    try:
        run_indicator(DEFINITION, extractor, supabase, dry_run=False)
    finally:
        pipeline_module.max_allowed_year = original

    written_years = {row["year"] for row in supabase.written_rows}
    assert written_years == {2027}  # 2031 escluso, troppo lontano


def test_run_indicator_deletes_existing_rows_beyond_new_projection_cutoff():
    # Righe già scritte in passato (quando pubblicavamo proiezioni fino al
    # 2031) devono essere ripulite, non lasciate orfane in tabella.
    observations = [
        RawObservation(source_indicator="X", source_name="International Monetary Fund",
                        country_code="SMR", year=2027, value=1.3, is_estimate=True),
    ]
    extractor = _StubExtractor(observations)
    existing = [
        {"id": 1, "year": 2027, "value_display": "1.3", "unit_display": "%",
         "conversion_note": None, "indicator_it": DEFINITION.indicator_it},
        {"id": 2, "year": 2030, "value_display": "1.3", "unit_display": "%",
         "conversion_note": None, "indicator_it": DEFINITION.indicator_it},
        {"id": 3, "year": 2031, "value_display": "1.3", "unit_display": "%",
         "conversion_note": None, "indicator_it": DEFINITION.indicator_it},
    ]
    supabase = _StubSupabase(existing_rows=existing)

    import oesm_pipeline.pipeline as pipeline_module
    original = pipeline_module.max_allowed_year
    pipeline_module.max_allowed_year = lambda today=None: 2027
    try:
        report = run_indicator(DEFINITION, extractor, supabase, dry_run=False)
    finally:
        pipeline_module.max_allowed_year = original

    assert set(supabase.deleted_ids) == {2, 3}
    assert report.deleted == 2

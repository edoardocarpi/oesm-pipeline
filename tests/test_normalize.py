from oesm_pipeline.normalize import currency, formatting


def test_format_value_display_none_becomes_none_not_string_null():
    # Punto centrale del documento di riferimento: NULL vero, mai "null" testuale.
    assert formatting.format_value_display(None) is None


def test_format_value_display_uses_dot_decimal_no_thousands_separator():
    assert formatting.format_value_display(1875136740.1) == "1875136740.1"


def test_is_technical_code_detects_lowercase_no_space():
    # Lo stesso bug trovato nei dati reali: "no_conversion_needed" e "projection"
    # sono entrambi invisibili sul sito perché minuscoli e senza spazi.
    assert formatting.is_technical_code("no_conversion_needed") is True
    assert formatting.is_technical_code("projection") is True


def test_is_technical_code_accepts_real_sentences():
    assert formatting.is_technical_code("Proiezione FMI, World Economic Outlook aprile 2026") is False


def test_currency_none_mode_passes_value_through():
    result = currency.convert(173.068169, "none", year=2023)
    assert result.value_eur == 173.068169
    assert result.eur_rate_used is None


def test_currency_already_eur_mode_rounds_and_documents():
    result = currency.convert(1874874703.1234, "already_eur", year=2023)
    assert result.value_eur == 1874874703.12
    assert "EUR" in result.conversion_note
    # La nota deve essere leggibile, non un codice tecnico da nascondere.
    assert " " in result.conversion_note


def test_currency_not_applicable_mode_never_writes_value_eur():
    # PPP non è una conversione di cambio (IMF.PPPPC): non forzarla in value_eur.
    result = currency.convert(70187.0, "not_applicable", year=2026)
    assert result.value_eur is None


def test_currency_none_value_short_circuits():
    result = currency.convert(None, "already_eur", year=2023)
    assert result.value_eur is None
    assert result.conversion_note is None


def test_currency_needs_rate_converts_with_real_annual_average():
    # 2823000000 USD (2,823 miliardi) al tasso 2025 (1.1306 USD per EUR)
    result = currency.convert(2823000000, "needs_rate", year=2025)
    assert result.eur_rate_used == 1.1306
    assert result.value_eur == round(2823000000 / 1.1306, 2)
    assert "BCE" in result.conversion_note
    assert " " in result.conversion_note  # frase leggibile, non codice tecnico


def test_currency_needs_rate_returns_none_for_future_projection_year():
    # 2028 è una proiezione: nessun tasso di cambio medio annuo è mai esistito.
    result = currency.convert(1000.0, "needs_rate", year=2028)
    assert result.value_eur is None
    assert result.eur_rate_used is None
    assert "non disponibile" in result.conversion_note


def test_currency_needs_rate_returns_none_before_euro_existed():
    result = currency.convert(1000.0, "needs_rate", year=1995)
    assert result.value_eur is None


def test_currency_needs_rate_respects_injected_rate_lookup_for_tests():
    result = currency.convert(110.0, "needs_rate", year=2025, rate_lookup=lambda y: 1.1)
    assert result.value_eur == 100.0
    assert result.eur_rate_used == 1.1

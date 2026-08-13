from oesm_pipeline.storage.diff import DiffAction, compute_diff


def test_new_year_is_insert():
    candidate = [{"year": 2025, "value_display": "1.2", "unit_display": "%", "conversion_note": None}]
    existing = []

    results = compute_diff(candidate, existing)

    assert results[0].action == DiffAction.INSERT
    assert results[0].existing_id is None


def test_identical_value_is_skipped_not_rewritten():
    # Questo è IL test che protegge il monitor homelab: un valore identico
    # non deve produrre una scrittura, altrimenti il trigger set_updated_at()
    # farebbe credere ai dati "freschi" anche senza nulla di nuovo dalla fonte.
    candidate = [{"year": 2024, "value_display": "1.2", "unit_display": "%", "conversion_note": None}]
    existing = [{"id": 42, "year": 2024, "value_display": "1.2", "unit_display": "%", "conversion_note": None}]

    results = compute_diff(candidate, existing)

    assert results[0].action == DiffAction.SKIP
    assert results[0].existing_id == 42


def test_changed_value_is_update():
    candidate = [{"year": 2024, "value_display": "1.5", "unit_display": "%", "conversion_note": None}]
    existing = [{"id": 42, "year": 2024, "value_display": "1.2", "unit_display": "%", "conversion_note": None}]

    results = compute_diff(candidate, existing)

    assert results[0].action == DiffAction.UPDATE
    assert results[0].existing_id == 42


def test_type_mismatch_alone_is_not_treated_as_change():
    # '1.2' (stringa dal DB) vs 1.2 (numero) non è un cambiamento di valore reale.
    candidate = [{"year": 2024, "value_display": 1.2, "unit_display": "%", "conversion_note": None}]
    existing = [{"id": 42, "year": 2024, "value_display": "1.2", "unit_display": "%", "conversion_note": None}]

    results = compute_diff(candidate, existing)

    assert results[0].action == DiffAction.SKIP


def test_unit_display_change_alone_triggers_update():
    # Correzione metodologica (es. cambio unità) va scritta anche a valore invariato.
    candidate = [{"year": 2023, "value_display": "100.0", "unit_display": "EUR", "conversion_note": None}]
    existing = [{"id": 1, "year": 2023, "value_display": "100.0", "unit_display": "USD", "conversion_note": None}]

    results = compute_diff(candidate, existing)

    assert results[0].action == DiffAction.UPDATE


def test_indicator_it_change_alone_triggers_update():
    # Correzione editoriale dell'etichetta (es. accorciare un nome troppo lungo)
    # deve propagarsi anche se valore, unità e nota restano identici — altrimenti
    # cambiare config/indicators.yaml non ha alcun effetto sui dati già scritti.
    candidate = [{"year": 2024, "value_display": "1.2", "unit_display": "%",
                  "conversion_note": None, "indicator_it": "Inflazione IPC (FMI)"}]
    existing = [{"id": 5, "year": 2024, "value_display": "1.2", "unit_display": "%",
                 "conversion_note": None, "indicator_it": "Inflazione IPC, media annua (%) — FMI"}]

    results = compute_diff(candidate, existing)

    assert results[0].action == DiffAction.UPDATE

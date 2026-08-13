import json
from pathlib import Path

import httpx
import pytest

from oesm_pipeline.extractors.imf import IMFExtractor
from oesm_pipeline.extractors.worldbank import WorldBankExtractor

FIXTURES = Path(__file__).parent / "fixtures"


def _mock_client(fixture_path: Path) -> httpx.Client:
    payload = json.loads(fixture_path.read_text())

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_imf_extractor_parses_values_and_flags_estimates():
    client = _mock_client(FIXTURES / "imf_pcpipch_smr.json")
    extractor = IMFExtractor(estimates_start_year=2026, client=client)

    observations = extractor.fetch("PCPIPCH", "SMR")

    assert len(observations) == 7
    by_year = {o.year: o for o in observations}

    assert by_year[2024].value == pytest.approx(1.2)
    assert by_year[2024].is_estimate is False  # prima del cutoff

    assert by_year[2026].value == pytest.approx(2.0)
    assert by_year[2026].is_estimate is True  # dal cutoff configurato in avanti

    assert by_year[2025].is_estimate is False  # 2025 è ancora sotto il cutoff 2026


def test_imf_extractor_returns_empty_list_when_country_missing():
    payload = {"values": {"PCPIPCH": {}}}  # nessun dato per SMR

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    extractor = IMFExtractor(estimates_start_year=2026, client=client)

    assert extractor.fetch("PCPIPCH", "SMR") == []


def test_worldbank_extractor_parses_rows_and_handles_null_values():
    client = _mock_client(FIXTURES / "wb_gdp_smr.json")
    extractor = WorldBankExtractor(client=client)

    observations = extractor.fetch("NY.GDP.MKTP.CN", "SMR")

    assert len(observations) == 3
    by_year = {o.year: o for o in observations}

    assert by_year[2023].value == pytest.approx(1874874703)
    assert by_year[2024].value is None  # WB pubblica righe anche senza valore

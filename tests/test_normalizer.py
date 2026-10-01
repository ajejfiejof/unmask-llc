"""Unit tests for text and address normalization functions."""

from unmask_llc.core.normalizer import (
    normalize_address,
    normalize_company_name,
    normalize_person_name,
    generate_address_hash,
)


def test_normalize_address():
    assert normalize_address("1230 Market St, Suite 400") == "1230 MARKET STREET STE 400"
    assert normalize_address("400 Fayetteville Rd.") == "400 FAYETTEVILLE ROAD"
    assert normalize_address("550 S. Mission Bay Blvd #12") == "550 SOUTH MISSION BAY BOULEVARD STE 12"


def test_normalize_company_name():
    assert normalize_company_name("Pacific Apex Holdings LLC") == "PACIFIC APEX HOLDINGS LLC"
    assert normalize_company_name("Pacific Apex Holdings LLC", strip_suffixes=True) == "PACIFIC APEX"
    assert normalize_company_name("Tarheel Capital Equity Partners, L.L.C.", strip_suffixes=True) == "TARHEEL CAPITAL EQUITY"


def test_normalize_person_name():
    assert normalize_person_name("Sterling, Marcus V.") == "MARCUS V STERLING"
    assert normalize_person_name("John Smith") == "JOHN SMITH"


def test_generate_address_hash():
    h1 = generate_address_hash("450 Mission St Ste 1200", "San Francisco", "CA", "94105")
    h2 = generate_address_hash("450 Mission Street Suite 1200", "San Francisco", "CA", "94105-1234")
    assert h1 == h2

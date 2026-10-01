"""Text and address normalization utilities for entity resolution."""

import re
import hashlib


def normalize_address(address_str: str) -> str:
    """Standardizes street address strings for consistent matching."""
    if not address_str:
        return ""

    addr = address_str.upper().strip()

    # Pre-process unit indicators like #
    addr = re.sub(r"#\s*", "STE ", addr)

    # Replace punctuation with spaces
    addr = re.sub(r"[^\w\s]", " ", addr)

    # Standardize abbreviations
    substitutions = [
        (r"\bST\b|\bSTREET\b", "STREET"),
        (r"\bAVE\b|\bAVENUE\b", "AVENUE"),
        (r"\bBLVD\b|\bBOULEVARD\b", "BOULEVARD"),
        (r"\bRD\b|\bROAD\b", "ROAD"),
        (r"\bDR\b|\bDRIVE\b", "DRIVE"),
        (r"\bLN\b|\bLANE\b", "LANE"),
        (r"\bCT\b|\bCOURT\b", "COURT"),
        (r"\bPL\b|\bPLACE\b", "PLACE"),
        (r"\bPKWY\b|\bPARKWAY\b", "PARKWAY"),
        (r"\bSTE\b|\bSUITE\b|\bAPT\b|\bAPARTMENT\b|\bUNIT\b", "STE"),
        (r"\bN\b|\bNORTH\b", "NORTH"),
        (r"\bS\b|\bSOUTH\b", "SOUTH"),
        (r"\bE\b|\bEAST\b", "EAST"),
        (r"\bW\b|\bWEST\b", "WEST"),
        (r"\bNE\b|\bNORTHEAST\b", "NORTHEAST"),
        (r"\bNW\b|\bNORTHWEST\b", "NORTHWEST"),
        (r"\bSE\b|\bSOUTHEAST\b", "SOUTHEAST"),
        (r"\bSW\b|\bSOUTHWEST\b", "SOUTHWEST"),
    ]

    for pattern, replacement in substitutions:
        addr = re.sub(pattern, replacement, addr, flags=re.IGNORECASE)

    # Collapse multiple spaces
    addr = re.sub(r"\s+", " ", addr).strip()
    return addr


def normalize_company_name(name_str: str, strip_suffixes: bool = False) -> str:
    """Standardizes corporate entity names."""
    if not name_str:
        return ""

    name = name_str.upper().strip()

    # Pre-clean dotted abbreviations (L.L.C. -> LLC, Inc. -> INC)
    name = re.sub(r"\bL\.?\s*L\.?\s*C\.?\b", "LLC", name)
    name = re.sub(r"\bL\.?\s*P\.?\b", "LP", name)
    name = re.sub(r"\bINC\.?\b", "INC", name)
    name = re.sub(r"\bCORP\.?\b", "CORP", name)
    name = re.sub(r"\bCO\.?\b", "CO", name)

    name = re.sub(r"[^\w\s]", " ", name)

    if strip_suffixes:
        suffixes = [
            r"\bLLC\b",
            r"\bLIMITED LIABILITY COMPANY\b",
            r"\bINC\b",
            r"\bINCORPORATED\b",
            r"\bCORP\b",
            r"\bCORPORATION\b",
            r"\bLP\b",
            r"\bLIMITED PARTNERSHIP\b",
            r"\bCO\b",
            r"\bCOMPANY\b",
            r"\bHOLDINGS\b",
            r"\bPROPERTIES\b",
            r"\bENTERPRISES\b",
            r"\bINVESTMENTS\b",
            r"\bPARTNERS\b",
            r"\bREALTY\b",
            r"\bMANAGEMENT\b",
            r"\bGROUP\b",
        ]
        for suffix in suffixes:
            name = re.sub(suffix, "", name, flags=re.IGNORECASE)

    name = re.sub(r"\s+", " ", name).strip()
    return name


def normalize_person_name(name_str: str) -> str:
    """Standardizes person names (handling 'LastName, FirstName Middle')."""
    if not name_str:
        return ""

    name = name_str.upper().strip()
    if "," in name:
        parts = name.split(",", 1)
        name = f"{parts[1].strip()} {parts[0].strip()}"

    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def generate_address_hash(street: str, city: str, state: str, zip_code: str) -> str:
    """Generates a deterministic hash for normalized address tuples."""
    norm_street = normalize_address(street)
    norm_city = city.upper().strip()
    norm_state = state.upper().strip()
    norm_zip = zip_code.strip()[:5]

    canonical = f"{norm_street}|{norm_city}|{norm_state}|{norm_zip}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

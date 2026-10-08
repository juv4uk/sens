#!/usr/bin/env python3
"""Strict SOURCE SCOPE, not semantic admission, for SENS T5 migration.

Historical benchmark measurement input is not an active application. This
classifier describes repo role only; it cannot mint function identities or
authorize executable physical .sens publication.
"""
from __future__ import annotations

from pathlib import PurePosixPath
import re


def archived_program_path(path: str) -> bool:
    """Only benchmarks/sens-surface/results/YYYYMMDD-id/programs/name.lisp."""
    if path.startswith("/") or "\\" in path:
        return False
    segments = PurePosixPath(path).parts
    return (
        len(segments) == 6
        and segments[:3] == ("benchmarks", "sens-surface", "results")
        and bool(re.fullmatch(r"[0-9]{8}-[A-Za-z0-9._-]+", segments[3]))
        and segments[4] == "programs"
        and segments[5] not in ("", ".", "..")
        and segments[5].endswith(".lisp")
        and all(segment not in (".", "..") for segment in path.split("/"))
    )


def source_scope(path: str) -> str:
    """No inference that an unknown/nonarchive Lisp is executable."""
    if archived_program_path(path):
        return "ARCHIVED_BENCHMARK_NONPROGRAM"
    return "UNCLASSIFIED_MAY_NEED_EXECUTABLE_PROOF"


def blocker_cohort(reason: str) -> str:
    """Actionable FIRST diagnostic grouping, not a semantic equivalence map."""
    if reason.startswith("ambiguous W8 executable head "):
        return "W8_ERA_PROVENANCE"
    if reason.startswith("legacy-unmapped SID8/Sens8 "):
        return "HISTORICAL_SUCCESSOR_LAW"
    if reason.startswith("legacy-unmapped my-lisp function "):
        if "'print'" in reason or "'read'" in reason:
            return "HOST_IO_EFFECT_ORACLE"
        return "CALLABLE_IDENTITY_AUTHORITY"
    if reason.startswith("word ") or "D2 word " in reason:
        return "TYPED_WORD_OR_D2_GRAMMAR"
    if "backquote" in reason or "unquote" in reason:
        return "SYNTAX_EXTENSION_LAW"
    if "closing parenthesis" in reason or "unterminated" in reason or "dotted pair" in reason:
        return "SOURCE_PARSE_OR_NONPROGRAM_DATA"
    if "missing" in reason:
        return "SOURCE_FORMAT_OR_UNKNOWN"
    return "NEEDS_SOURCE_CLASSIFICATION"

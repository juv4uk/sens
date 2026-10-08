#!/usr/bin/env python3
"""Source-scope only: classify immutable archived benchmark Lisp inputs.

Mirrors path law proven by #4492. NEVER grants executable D1-D9 semantics,
owner identity, Rust D2 admission, or permission to publish a .sens file.
Everything outside this exact archive pattern stays UNCLASSIFIED.
"""
from pathlib import PurePosixPath
import re


def archived_benchmark_source(path: str) -> bool:
    if not isinstance(path, str) or path.startswith("/") or "\\" in path:
        return False
    parts = PurePosixPath(path).parts
    return (
        len(parts) == 6
        and parts[:3] == ("benchmarks", "sens-surface", "results")
        and bool(re.fullmatch(r"[0-9]{8}-[A-Za-z0-9._-]+", parts[3]))
        and parts[4] == "programs"
        and parts[5] not in ("", ".", "..")
        and parts[5].endswith(".lisp")
        and all(p not in (".", "..") for p in path.split("/"))
    )


def scope(path: str) -> str:
    return ("ARCHIVED_BENCHMARK_NONPROGRAM" if archived_benchmark_source(path)
            else "UNCLASSIFIED_NEEDS_SOURCE_PROOF")

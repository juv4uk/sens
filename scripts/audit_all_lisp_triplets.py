#!/usr/bin/env python3
"""Суцільний облік .lisp -> .sens -> двійкового перегляду.

Усі каталоги входять до знаменника, зокрема історичні та тестові.
Наявність файлів НЕ є доказом зворотності. --verify-bounded запускає
справжній обмежений перевірник трійок (D1/D2/D3 та доведений D4);
непідтримувані форми залишаються BLOCKED, а не PASS.
Навіть 100% обмеженої зворотності не доводять виконання SENS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from report_ukr_projection_progress import examine_file, examine_source_projection, tokenize_lisp

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "sens-all-lisp-reversibility-census/v1"


def misnamed_binary_d2(path: Path) -> bool:
    """Двійкові слова D2 повинні мати .bits, а не .lisp."""
    words = path.read_bytes().split()
    return (len(words) >= 3
            and all(word and not word.strip(b"01") for word in words)
            and b"10" in words and (b"00" in words or b"01" in words))



def reviewed_nonprogram_pins(root: Path) -> dict[str, tuple[str, str]]:
    """Визнати лише явно перевірені, SHA-закріплені файли даних.

    Схема / число записів / Git blob кожного джерела перевіряються
    окремо. Відсутній чи пошкоджений маніфест НЕ звільняє файли
    від обліку програм. Це не SENS semantic oracle.
    """
    from report_original_migration_candidates import NONPROGRAM_MANIFESTS

    approved: dict[str, tuple[str, str]] = {}
    for cohort, manifest_name, count in NONPROGRAM_MANIFESTS:
        path = root / manifest_name
        if path.is_symlink() or not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            continue
        rows = data.get("entries")
        if (data.get("schema") != "sens-migration-nonprogram-manifest-1"
                or data.get("issue") != 4460
                or data.get("automatic_sens_companion") is not False
                or not isinstance(rows, list) or len(rows) != count):
            continue
        staged: dict[str, tuple[str, str]] = {}
        valid = True
        for row in rows:
            if not isinstance(row, dict):
                valid = False
                break
            name, sha = row.get("path"), row.get("git_blob_sha1")
            if (not isinstance(name, str) or not name.endswith(".lisp")
                    or name.startswith("/") or "\\" in name
                    or any(part in ("", ".", "..") for part in name.split("/"))
                    or not isinstance(sha, str) or len(sha) != 40
                    or any(char not in "0123456789abcdef" for char in sha)
                    or name in approved or name in staged):
                valid = False
                break
            staged[name] = (sha, cohort)
        if valid:
            approved.update(staged)
    return approved


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def scan(root: Path, *, verify_bounded: bool = False, validator=None, limit: int = 20) -> dict:
    if not root.is_dir():
        raise NotADirectoryError(root)
    if limit < 0:
        raise ValueError("limit має бути невід'ємним")
    root = root.resolve()
    sources = sorted(
        (p for p in root.rglob("*.lisp")
         if not ({".git", ".worktrees"} & set(p.relative_to(root).parts))),
        key=lambda p: p.relative_to(root).as_posix(),
    )
    reviewed_pins = reviewed_nonprogram_pins(root)
    if verify_bounded and validator is None:
        from verify_uk_t5_t5m_triplet import verify
        # Поточний фізичний носій T5M, старий T5 — лише явний аудит.
        validator = lambda source, physical, view: verify(
            source, physical, view, codec="t5m"
        )

    def require_bounded_receipt(witness: object, source: Path, physical: Path, view: Path) -> str:
        """Read-only integrity of the real bounded oracle receipt, never runtime GO."""
        if not isinstance(witness, dict):
            raise ValueError("немає структурованого доказу")
        if (witness.get("schema") != "sens-uk-t5-view-bounded-proof/v1"
                or witness.get("status") != "BOUNDED_TRIPLE_PARITY_ONLY_NOT_RELEASE_ADMISSION"):
            raise ValueError("непідтверджена схема або статус обмеженого свідка")
        for key in ("canonical_uk_roundtrip", "program_identity_roundtrip",
                    "canonical_view_roundtrip"):
            if witness.get(key) is not True:
                raise ValueError("не доведено " + key)
        codec = witness.get("physical_codec")
        expected_codec_flag = {
            "t5": "physical_T5_roundtrip",
            "t5m": "physical_T5M_roundtrip",
        }.get(codec)
        if (expected_codec_flag is None
                or witness.get(expected_codec_flag) is not True
                or witness.get("physical_T5_roundtrip") is (codec == "t5m")
                or witness.get("physical_T5M_roundtrip") is (codec == "t5")):
            raise ValueError("не доведено обертання фактичного T5/T5M носія")
        for key, expected in (("source", source), ("sens", physical), ("view", view)):
            if witness.get(key) != str(expected):
                raise ValueError("свідок посилається на інший файл: " + key)
        for key, file in (("source_sha256", source), ("physical_sha256", physical),
                          ("view_sha256", view)):
            expected = hashlib.sha256(file.read_bytes()).hexdigest()
            if witness.get(key) != expected:
                raise ValueError("зміст файла розходиться зі свідком: " + key)
        typed = witness.get("typed_word_sha256")
        if (not isinstance(typed, str) or len(typed) != 64
                or any(char not in "0123456789abcdef" for char in typed)
                or type(witness.get("typed_word_count")) is not int
                or witness["typed_word_count"] < 1):
            raise ValueError("свідок не містить коректних точнодоменних слів")
        if (witness.get("runtime_oracle_admitted_by_this_audit") is not False
                or witness.get("old_originals_migrated_by_this_audit") != 0):
            raise ValueError("механічний свідок не дозволяє семантичний або релізний допуск")
        return codec

    # Лексичний облік, а не підрахунок рядків: вкладені #| ... |#
    # і ;коментарі не створюють програму, навіть із дужками всередині.
    # Незакриті коментарі, неправильний UTF-8 і справжні форми
    # залишаються в обліку потенційних програм, а не звільняються.
    def only_line_comments(file: Path) -> bool:
        try:
            return not tokenize_lisp(file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            return False

    # Не прирівнюємо історичний T5 до сучасного фізичного T5M.
    counts = dict(ukrainian_keyboard=0, with_sens=0, with_view=0,
                  complete_triplets=0, bounded_verified=0,
                  misnamed_binary_lisp=0, undecidable_lisp_files=0,
                  comment_only_nonprogram_lisp=0,
                  reviewed_nonprogram_lisp=0, reviewed_nonprogram_pin_drift=0,
                  unapproved_nonprogram_physical=0, nonprogram_style_warnings=0,
                  potential_program_files=0, potential_program_missing_sens=0,
                  comment_only_style_warnings=0,
                  comment_only_with_physical=0,
                  program_style_warnings=0,
                  invalid_program_source_projection=0,
                  bounded_verified_t5m=0, bounded_verified_legacy_t5=0)
    blocked: list[dict[str, str]] = []

    def reject(path: str, reason: str) -> None:
        blocked.append({"path": path, "reason": reason})

    for source in sources:
        relative = source.relative_to(root).as_posix()
        # Never follow a symlink, even when its target looks valid.
        if source.is_symlink() or not source.is_file():
            counts["undecidable_lisp_files"] += 1
            reject(relative, "не звичайний файл Lisp")
            continue
        comment_only = only_line_comments(source)
        pinned = reviewed_pins.get(relative)
        reviewed_ok = bool(pinned and git_blob_sha(source.read_bytes()) == pinned[0])
        if pinned and not reviewed_ok:
            counts["reviewed_nonprogram_pin_drift"] += 1
            reject(relative, "SHA затверджених Lisp-даних змінився; потрібна пофайлова перевірка")
        keyboard_problem = examine_file(source)
        if keyboard_problem is None:
            counts["ukrainian_keyboard"] += 1
        elif reviewed_ok:
            # Схвалені незмінні дані не є кодом: латиниця у
            # зовнішніх протокольних рядках — стиль, не runtime RED.
            counts["nonprogram_style_warnings"] += 1
        elif comment_only:
            # Стиль коментаря або порожнього профілю -- телеметрія,
            # а НЕ семантичний блокер: виконуваного коду тут немає.
            counts["comment_only_style_warnings"] += 1
        else:
            # Коментарі та цитовані протокольні дані не є викличним кодом.
            # Стиль усього файла лишається в обліку, але не дає
            # фальшивого BLOCK для справжнього Lisp/T5M-свідка.
            # На відміну від стилю, неукраїнські виконувані імена та
            # пошкоджена Lisp-структура залишаються конкретним дефектом.
            source_problem = examine_source_projection(source)
            if source_problem is None:
                counts["program_style_warnings"] += 1
            else:
                counts["invalid_program_source_projection"] += 1
                reject(relative, "виконувана Lisp-проєкція: " + source_problem)
        binary_disguised = misnamed_binary_d2(source)
        if binary_disguised:
            counts["misnamed_binary_lisp"] += 1
            reject(relative, "двійкові слова D2 під розширенням .lisp; потрібен .bits")
        physical = source.with_suffix(".sens")
        view = source.with_suffix("")
        has_sens = physical.is_file() and not physical.is_symlink()
        has_view = view.is_file() and not view.is_symlink()
        counts["with_sens"] += int(has_sens)
        counts["with_view"] += int(has_view)
        # Коментарний профіль без програмного змісту не вимагає T5M,
        # але вже створений фізичний носій мусить залишитися помітним.
        if comment_only:
            counts["comment_only_nonprogram_lisp"] += 1
            if physical.exists() or physical.is_symlink():
                counts["comment_only_with_physical"] += 1
                reject(relative, "файл лише з коментарів має необґрунтований .sens")
            continue
        # Вже схвалена данна/схема/таблиця не є виконуваною формою.
        # Жодного нового дозволу: лише точний Git blob з #4460.
        if reviewed_ok:
            counts["reviewed_nonprogram_lisp"] += 1
            if physical.exists() or physical.is_symlink():
                counts["unapproved_nonprogram_physical"] += 1
                reject(relative, "затверджені Lisp-дані мають недопущений .sens")
            continue
        counts["potential_program_files"] += 1
        if not has_sens:
            counts["potential_program_missing_sens"] += 1
            reject(relative, "немає звичайного однойменного .sens")
            continue
        if not has_view:
            reject(relative, "немає звичайного двійкового перегляду")
            continue
        counts["complete_triplets"] += 1
        if verify_bounded and not binary_disguised:
            try:
                witness = validator(source, physical, view)
                codec = require_bounded_receipt(witness, source, physical, view)
            except (OSError, ValueError, UnicodeError) as exc:
                reject(relative, "обмежена зворотність BLOCKED: " + str(exc))
            else:
                counts["bounded_verified"] += 1
                counts["bounded_verified_t5m" if codec == "t5m"
                       else "bounded_verified_legacy_t5"] += 1

    all_verified = counts["potential_program_files"] > 0 and (
        counts["bounded_verified"] == counts["potential_program_files"]
        and counts["bounded_verified_t5m"] == counts["potential_program_files"]
        # Keyboard style is a separate source-quality metric. Comments,
        # whitespace and quoted external protocol data are not executable
        # program identity; do not let them veto proved roundtrips.
        and counts["misnamed_binary_lisp"] == 0
        and counts["invalid_program_source_projection"] == 0
        # Відхилений .lisp (зокрема симлінк) не може зникнути
        # зі знаменника й дати хибний загальний PASS.
        and counts["undecidable_lisp_files"] == 0
        and counts["reviewed_nonprogram_pin_drift"] == 0
        and counts["unapproved_nonprogram_physical"] == 0
        and counts["comment_only_with_physical"] == 0
        and verify_bounded
    )
    # Окремий точний показник для поточного T5M. Історичний T5
    # залишається фізично оберненим, але не доводить завершення міграції.
    all_current_t5m_verified = (
        all_verified
        and counts["bounded_verified_t5m"] == counts["potential_program_files"]
        and counts["bounded_verified_legacy_t5"] == 0
    )
    return {
        "schema": SCHEMA,
        "total_lisp_files": len(sources),
        **counts,
        # Загальна відсутність фізичних пар і виконавчий борг різні:
        # коментарні файли тут НЕ утворюють штучний semantic BLOCK.
        "missing_sens": len(sources) - counts["with_sens"],
        "missing_complete_triplet": len(sources) - counts["complete_triplets"],
        "unverified_triplets": counts["complete_triplets"] - counts["bounded_verified"],
        "verification_requested": verify_bounded,
        "all_bounded_reverse_verified": all_verified,
        "all_current_t5m_bounded_reverse_verified": all_current_t5m_verified,
        "current_t5m_without_bounded_proof": (
            counts["potential_program_files"] - counts["bounded_verified_t5m"]
        ),
        "semantic_runtime_proven": False,
        "release_ready": False,
        "release_decision": "NO-GO: потрібні докази виконання SENS та повної семантики",
        # Кількість діагностик може перевищувати число різних файлів.
        # Облік інформативний, не додає жодних нових release gate.
        "blocked_count": len(blocked),
        "blocked_file_count": len({row["path"] for row in blocked}),
        "potential_program_missing_complete_triplet": (
            counts["potential_program_files"] - counts["complete_triplets"]
        ),
        "potential_program_without_bounded_proof": (
            counts["potential_program_files"] - counts["bounded_verified"]
        ),
        "blocked_sample": blocked[:limit],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--verify-bounded", action="store_true")
    parser.add_argument("--require-reversible", action="store_true",
                        help="вимагати обмеженої зворотності виконуваних Lisp саме в чинному T5M")
    args = parser.parse_args(argv)
    try:
        result = scan(args.root, verify_bounded=args.verify_bounded, limit=args.limit)
    except (OSError, ValueError) as exc:
        print("CENSUS_BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.json:
        args.json.write_text(text, encoding="utf-8")
    if args.require_reversible and not result["all_current_t5m_bounded_reverse_verified"]:
        print("REVERSE_BLOCKED: неповне покриття чинного T5M або недоведена зворотність",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

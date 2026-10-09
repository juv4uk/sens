#!/usr/bin/env python3
"""Дослідницькі математичні свідки D10; не native SENS/донорський оракул."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "knowledge/d10-linguistic-law-intake-20261009.json"
VOWELS = set("аеєиіїоуюяАЕЄИІЇОУЮЯ")
LETTERS = set("абвгґдеєжзиіїйклмнопрстуфхцчшщьюя")
CONSONANTS = set("бвгґджзйклмнпрстфхцчшщ")
APOSTROPHES = set("'\u2019\u02bc")
MARK = "\u0301"

def positions(source):
    seen = set()
    ordinal = 0
    for i, char in enumerate(source):
        if char in VOWELS:
            ordinal += 1
        elif char == MARK:
            if i == 0 or source[i - 1] not in VOWELS or ordinal in seen:
                raise ValueError("acute must follow a previously unmarked vowel")
            seen.add(ordinal)
    return seen

def stress_transfer(source, target):
    if MARK in target:
        raise ValueError("target already contains stress")
    marked = positions(source)
    if marked and max(marked) > sum(c in VOWELS for c in target):
        raise ValueError("target has insufficient vowels")
    output = []
    syll = 0
    for ch in target:
        output.append(ch)
        if ch in VOWELS:
            syll += 1
            if syll in marked:
                output.append(MARK)
    return "".join(output)

def context_rewrite(source, default, start=None, multi=None, after_consonant=None):
    start = start or {}
    multi = multi or {}
    after_consonant = after_consonant or {}
    if any(not k or len(k) < 2 for k in multi):
        raise ValueError("invalid multi-key")
    out = []
    i = 0
    while i < len(source):
        char = source[i]
        word_start = i == 0 or source[i-1] not in LETTERS | APOSTROPHES
        if word_start and char in start:
            out.append(start[char])
            i += 1
            continue
        matches = [k for k in multi if source.startswith(k, i)]
        if matches:
            key = max(matches, key=len)
            out.append(multi[key])
            i += len(key)
            continue
        if i > 0 and source[i-1] in CONSONANTS and char in after_consonant:
            out.append(after_consonant[char])
        else:
            out.append(default.get(char, char))
        i += 1
    return "".join(out)

def check_dossier(doc):
    assert doc["schema"] == "d10-linguistic-law-intake/v1"
    assert doc["status"] == "RESEARCH-NOT-SELECTED"
    assert doc["baseline"] == {"selected": 630, "remaining": 394, "ratified": 0}
    assert doc["selection_delta"] == doc["ratified_delta"] == 0
    names = [p["semantic_name"] for p in doc["candidates"]]
    assert names == ["STRESS-SYLLABLE-TRANSFER","CONTEXTUAL-LONGEST-TRANSLITERATE"]
    for p in doc["candidates"]:
        assert p["decision"] == "HOLD-OWNER-REVIEW"
        assert p["coordinate"] is None and p["ratified"] is False
        assert p["positives"] and p["falsifier"] and p["dedup"]

def main():
    doc = json.loads(SRC.read_text(encoding="utf-8"))
    check_dossier(doc)
    assert stress_transfer("сло́во","СЛОВО") == "СЛО́ВО"
    assert stress_transfer("мо́ва́","МОВА") == "МО́ВА́"
    assert stress_transfer("СЛО́ВО","слово") == "сло́во"
    assert stress_transfer("мова","МОВА") == "МОВА"
    for a,b in [("м́ова","МОВА"),("моло́ко","КІТ"),("сло́во","СЛО́ВО")]:
        try: stress_transfer(a,b)
        except ValueError: pass
        else: raise AssertionError("invalid stress accepted")
    n = 0
    for length in range(1,9):
        for position in range(1,length+1):
            source = "а" * (position-1) + "а́" + "а" * (length-position)
            expected = "А" * (position-1) + "А́" + "А" * (length-position)
            assert stress_transfer(source, "А"*length) == expected
            n += 1
    assert context_rewrite("ї кї",{"ї":"ji","к":"k"},start={"ї":"yi"}) == "yi kji"
    assert context_rewrite("к'ї",{"ї":"ji","к":"k"},start={"ї":"yi"}) == "k'ji"
    assert context_rewrite("єїк єї",{"к":"k"},multi={"єїк":"zzz","єї":"xxx","їк":"yy"}) == "zzz xxx"
    assert context_rewrite("кя ая",{"к":"k","я":"ja","а":"a"},after_consonant={"я":"ia"}) == "kia aja"
    assert context_rewrite("?",{}) == "?"
    mutations = [
      lambda j:j.update(selection_delta=1),
      lambda j:j.update(ratified_delta=1),
      lambda j:j["candidates"][0].update(ratified=True),
      lambda j:j["candidates"][0].update(coordinate="0"*10),
      lambda j:j["candidates"][1].update(decision="SELECTED"),
      lambda j:j["candidates"][1].update(positives=[]),
    ]
    for mutate in mutations:
        changed = copy.deepcopy(doc)
        mutate(changed)
        try: check_dossier(changed)
        except AssertionError: pass
        else: raise AssertionError("mutation guard failed")
    print(f"D10-LINGUISTIC: PASS stress_grid={n} + 9 explicit witnesses; negative_mutations={len(mutations)}; selected=0 ratified=0")
    print("Native donor/SENS equality has not been established.")

if __name__ == "__main__":
    main()

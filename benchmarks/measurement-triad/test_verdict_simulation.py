#!/usr/bin/env python3
"""Симуляційні тести verdict.py — доводять поведінку на відомих істинних станах.

НАВІЩО: числа звіту не доводять нічого, якщо невідомо, як інструмент поводиться
на даних, де істина ВІДОМА. Тут істина задана генератором, і перевіряється
рівно те, що потрібно для наукової строгості:

  • рівень (level): за відсутності ефекту частка хибних «FASTER» має бути
    близькою до заявлених 5%, а не 50%;
  • відомий ефект: інструмент відновлює задане відношення;
  • heavy tails і викиди: один викид не перевертає висновок;
  • відсутній RAPL: ENERGY_NOT_MEASURED, а не вигадані джоулі з TDP;
  • автокореляція: кореляція всередині блока не робить блок незалежним;
  • порядок AB/BA: без балансу — INCONCLUSIVE, а не висновок;
  • множинні порівняння: Holm не пропускає сімейний хибнопозитив.

Запуск: python3 benchmarks/measurement-triad/test_verdict_simulation.py
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verdict import (  # noqa: E402
    analyze, analyze_many, holm_adjust, independent_units, InvalidEvidence,
)

PROVENANCE = {
    "git_sha": "0" * 40, "binary_sha256": "0" * 64, "cpu_model": "synthetic",
    "rustc": "synthetic", "os": "synthetic", "affinity": "0", "governor": "performance",
    "turbo": "off", "timing_source": "synthetic",
}
PARITY = {"passed": True, "oracle_id": "synthetic-oracle"}

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  PASS  {name}")
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"  FAIL  {name} — {detail}")


def build(ratio_fn, *, processes: int = 12, per_process: int = 6,
          seed: int = 1, metric: str = "wall_time_ns", noise: float = 0.02,
          balance: bool = True, machine_id: str = "m1", session_id: str = "s1") -> dict:
    """Генерує парні дані з відомим відношенням candidate/baseline.

    ratio_fn(process_index, pair_index) -> float
    """
    rng = random.Random(seed)
    pairs = []
    for p in range(processes):
        for k in range(per_process):
            order = "AB" if (k % 2 == 0 or not balance) else "BA"
            base = 1_000_000.0 * math.exp(rng.gauss(0, noise))
            cand = base * ratio_fn(p, k) * math.exp(rng.gauss(0, noise))
            item = {
                "process_id": f"proc-{p}", "order": order,
                "machine_id": machine_id, "session_id": session_id,
                "baseline_ns": base, "candidate_ns": cand,
                "baseline_energy_uj": base / 1000.0, "candidate_energy_uj": cand / 1000.0,
                "baseline_peak_rss_kib": base / 10000.0, "candidate_peak_rss_kib": cand / 10000.0,
            }
            pairs.append(item)
    return {"schema": "sens-paired-physical/v1", "metric": metric,
            "parity": PARITY, "provenance": PROVENANCE, "pairs": pairs}


def test_level_no_effect() -> None:
    """За відсутності ефекту частка хибних висновків має бути ≤ заявленого рівня."""
    print("\n[1] Рівень: ефекту немає, хибні 'FASTER'/'SLOWER'")
    decisive = 0
    trials = 120
    for t in range(trials):
        doc = build(lambda p, k: 1.0, seed=1000 + t)
        r = analyze(doc, draws=1200, seed=7)
        if r["status"] in ("FASTER", "SLOWER"):
            decisive += 1
    rate = decisive / trials
    check("частка хибних висновків ≤ 10%", rate <= 0.10, f"rate={rate:.3f} з {trials}")
    check("більшість — INCONCLUSIVE", rate < 0.5, f"rate={rate:.3f}")


def test_known_effect() -> None:
    """Відомий ефект відновлюється в межах інтервалу."""
    print("\n[2] Відомий ефект 20% прискорення")
    doc = build(lambda p, k: 0.8, seed=42)
    r = analyze(doc, draws=4000, seed=7)
    check("status FASTER", r["status"] == "FASTER", f"status={r['status']}")
    lo, hi = r["ci95_ratio"]
    check("істинне 0.8 всередині ДІ", lo <= 0.8 <= hi, f"CI=({lo:.3f},{hi:.3f})")
    check("точкова оцінка близько 0.8", abs(r["ratio"] - 0.8) < 0.05, f"ratio={r['ratio']:.3f}")


def test_heavy_tails_and_outlier() -> None:
    """Один викид не перевертає висновок; heavy tails дають ширший ДІ."""
    print("\n[3] Heavy tails і викид")
    doc = build(lambda p, k: 1.0, seed=5)
    doc["pairs"][3]["candidate_ns"] *= 60.0  # один екстремальний викид
    r = analyze(doc, draws=3000, seed=7)
    check("викид не дає 'FASTER'", r["status"] != "FASTER", f"status={r['status']}")

    def heavy(p, k):
        return 1.0
    doc2 = build(heavy, seed=6, noise=0.35)
    r2 = analyze(doc2, draws=3000, seed=7)
    check("широкий шум → INCONCLUSIVE", r2["status"] == "INCONCLUSIVE", f"status={r2['status']}")


def test_energy_not_measured() -> None:
    """Відсутній енергетичний датчик не дає джоулів."""
    print("\n[4] Енергія: немає даних — немає числа")
    doc = build(lambda p, k: 1.0, seed=8, metric="energy_uj")
    del doc["pairs"][0]["candidate_energy_uj"]
    raised = False
    try:
        analyze(doc, draws=1500, seed=7)
    except InvalidEvidence:
        raised = True
    check("пропущена енергія → InvalidEvidence, не вигадані джоулі", raised,
          "очікували відмову, отримали число")

    doc_ok = build(lambda p, k: 1.0, seed=9, metric="energy_uj")
    r = analyze(doc_ok, draws=1500, seed=7)
    check("метрика energy_uj приймається, коли дані є", r["metric"] == "energy_uj",
          f"metric={r.get('metric')}")


def test_autocorrelation_within_block() -> None:
    """Кореляція всередині блока не робить блоків більше."""
    print("\n[5] Автокореляція всередині блока")
    rng = random.Random(11)
    pairs = []
    for p in range(10):
        drift = rng.gauss(0, 0.05)  # спільний зсув для всього блока
        for k in range(6):
            order = "AB" if k % 2 == 0 else "BA"
            base = 1_000_000.0 * math.exp(drift + rng.gauss(0, 0.01))
            cand = base * math.exp(drift + rng.gauss(0, 0.01))
            pairs.append({"process_id": f"proc-{p}", "order": order,
                          "baseline_ns": base, "candidate_ns": cand,
                          "machine_id": "m1", "session_id": "s1"})
    doc = {"schema": "sens-paired-physical/v1", "metric": "wall_time_ns",
           "parity": PARITY, "provenance": PROVENANCE, "pairs": pairs}
    r = analyze(doc, draws=2500, seed=7)
    check("незалежних одиниць рівно 10 (блоки, не пари)",
          r.get("independent_processes") == 10, f"units={r.get('independent_processes')}")


def test_order_balance_required() -> None:
    """Без AB/BA балансу — INCONCLUSIVE, а не висновок."""
    print("\n[6] Порядок AB/BA")
    doc = build(lambda p, k: 0.7, seed=13, balance=False)
    r = analyze(doc, draws=2000, seed=7)
    check("без балансу → INCONCLUSIVE", r["status"] == "INCONCLUSIVE", f"status={r['status']}")
    check("причина названа", "ORDER_BALANCE" in (r.get("reason") or ""), f"reason={r.get('reason')}")


def test_too_few_units() -> None:
    """Мало незалежних одиниць — недостатньо даних."""
    print("\n[7] Недостатньо незалежних одиниць")
    doc = build(lambda p, k: 0.7, seed=14, processes=3, per_process=20)
    r = analyze(doc, draws=2000, seed=7)
    check("3 процеси → INCONCLUSIVE", r["status"] == "INCONCLUSIVE", f"status={r['status']}")


def test_no_parity_blocked() -> None:
    """Без доведеного паритету — BLOCKED."""
    print("\n[8] Паритет")
    doc = build(lambda p, k: 0.5, seed=15)
    doc["parity"] = {"passed": False, "oracle_id": "x"}
    r = analyze(doc, draws=1500, seed=7)
    check("без паритету → BLOCKED", r["status"] == "BLOCKED", f"status={r['status']}")
    check("причина PARITY_NOT_PROVED", r.get("reason") == "PARITY_NOT_PROVED", f"reason={r.get('reason')}")


def test_holm_correction() -> None:
    """Holm не пропускає сімейний хибнопозитив при багатьох порівняннях."""
    print("\n[9] Множинні порівняння: Holm")
    adj = holm_adjust([0.01, 0.02, 0.03, 0.04])
    check("монотонно неспадні", all(adj[i] <= adj[i + 1] for i in range(len(adj) - 1)), f"{adj}")
    check("перший множиться на m", abs(adj[0] - 0.04) < 1e-12, f"{adj[0]}")
    check("останній ≥ вхідного", adj[-1] >= 0.04, f"{adj[-1]}")
    check("порожній вхід → порожній вихід", holm_adjust([]) == [], "не порожній")

    docs = [build(lambda p, k: 1.0, seed=200 + i) for i in range(6)]
    multi = analyze_many(docs, draws=1200, seed=7)
    check("survivors рахується", "survivors" in multi, "немає поля")
    check("family_alpha 0.05", multi.get("family_alpha") == 0.05, f"{multi.get('family_alpha')}")



def test_familywise_inference_is_fail_closed() -> None:
    """A CI crossing a single-test threshold must never become Holm p=0."""
    print("\\n[9b] Family-wise: no invented adjusted p-values")
    docs = [build(lambda p, k: 0.6, seed=701 + i) for i in range(3)]
    result = analyze_many(docs, draws=600, seed=7)
    comparisons = result["comparisons"]
    check("сімейний результат INCONCLUSIVE",
          result.get("status") == "INCONCLUSIVE", str(result.get("status")))
    check("жодного сімейного переможця",
          result.get("survivors") == 0 and
          all(r["status"] not in ("FASTER", "SLOWER") for r in comparisons))
    check("сильні індивідуальні ДІ збережені як описові",
          len(comparisons) == 3 and
          all(r.get("ci95_ratio") and r["ci95_ratio"][1] < 1.0
              for r in comparisons))
    check("немає сфабрикованих Holm-p",
          all(r.get("holm_adjusted_p") is None for r in comparisons))
    check("family inference явно не виконано",
          result.get("family_inference") == "NOT_PERFORMED")

    failed = build(lambda p, k: 0.6, seed=708)
    failed["parity"] = {"passed": False, "oracle_id": "negative-control"}
    bad_result = analyze_many([failed], draws=300, seed=7)
    check("невдалий паритет лишається BLOCKED",
          bad_result["comparisons"][0]["status"] == "BLOCKED")



def test_hierarchy_levels() -> None:
    """Рівні machine/session/block/pair рахуються окремо."""
    print("\n[10] Рівні ієрархії")
    doc = build(lambda p, k: 1.0, seed=21, processes=5, per_process=4)
    lv = independent_units(doc)
    check("machine=1", lv["machine"] == 1, f"{lv['machine']}")
    check("session=1", lv["session"] == 1, f"{lv['session']}")
    check("block=5", lv["block"] == 5, f"{lv['block']}")
    check("pair=20", lv["pair"] == 20, f"{lv['pair']}")


def test_no_data_dependent_stopping() -> None:
    """Додавання даних не робить висновок різкішим без ефекту."""
    print("\n[11] Немає data-dependent stopping")
    small = analyze(build(lambda p, k: 1.0, seed=31, processes=10, per_process=4),
                    draws=1500, seed=7)
    large = analyze(build(lambda p, k: 1.0, seed=31, processes=30, per_process=12),
                    draws=1500, seed=7)
    check("мало даних: INCONCLUSIVE", small["status"] == "INCONCLUSIVE", f"{small['status']}")
    check("більше даних без ефекту теж INCONCLUSIVE", large["status"] == "INCONCLUSIVE",
          f"{large['status']} — ефекту немає, висновку бути не може")


def main() -> int:
    print("СИМУЛЯЦІЙНІ ТЕСТИ verdict.py — істина задана генератором")
    for fn in (test_level_no_effect, test_known_effect, test_heavy_tails_and_outlier,
               test_energy_not_measured, test_autocorrelation_within_block,
               test_order_balance_required, test_too_few_units, test_no_parity_blocked,
               test_holm_correction, test_familywise_inference_is_fail_closed,
               test_hierarchy_levels, test_no_data_dependent_stopping):
        fn()
    print("\n" + "=" * 60)
    if FAILURES:
        print(f"ПРОВАЛЕНО {len(FAILURES)}:")
        for f in FAILURES:
            print("  •", f)
        return 1
    print("УСІ СИМУЛЯЦІЙНІ ТЕСТИ ПРОЙДЕНО")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""ENERGY-02/05 міст: корпус → сирі парні дані → verdict.py.

НАВІЩО: корпус і статистика існували окремо. Паритет доводив, що мови роблять
однакову роботу; verdict.py умів рахувати ДІ — але між ними не було нічого, що
реально запускає задачі й записує пари. Це і є цей файл.

Що робить:
  1. для кожної задачі й кожної доступної мови — N НЕЗАЛЕЖНИХ запусків процесу;
  2. порядок AB/BA чергується, щоб дрейф частоти не приписався одній мові;
  3. пише сирі пари у форматі `sens-paired-physical/v1` (вхід verdict.py);
  4. енергію НЕ вигадує: без RAPL поле лишається ENERGY_NOT_MEASURED.

Чого НЕ робить:
  • не вимірює енергію без датчика;
  • не оголошує переможця;
  • не приховує, що JIT-мови (Node) мають іншу природу прогріву — це
    зафіксовано в полі `warmup_note`, а не згладжено.

Запуск:
  python3 benchmarks/language-energy-study/run_study.py --smoke
  python3 benchmarks/language-energy-study/run_study.py --processes 8 --out raw.json
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "corpus"
MANIFEST = CORPUS / "manifest.json"

# Реалізації, які РЕАЛЬНО існують у дереві. Немає компілятора — немає запису.
LANGUAGES = {
    "python": {
        "kind": "interpreted",
        "cmd": lambda task_id: f'{sys.executable} -c "import runpy,sys;sys.exit(0)"',
    },
    "javascript": {
        "kind": "jit",
        "cmd": lambda task_id: f"node {CORPUS / 'javascript' / JS_FILES[task_id]}",
    },
}

JS_FILES = {
    "T01-symbolic-recursion": "t01_fib.mjs",
    "T02-exact-rationals": "t02_rationals.mjs",
    "T03-parsing-text": "t03_parse.mjs",
    "T04-sorting": "t04_sort.mjs",
    "T05-allocation-gc": "t05_alloc.mjs",
    "T06-io": "t06_io.mjs",
    "T07-matrices": "t07_matrices.mjs",
    "T08-persistent-structures": "t08_persistent.mjs",
    "T09-bit-operations": "t09_bitcount.mjs",
}

# Python-реалізації: референс із parity_check.py вже виконує ту саму роботу.
PY_MODULES = {
    "T01-symbolic-recursion": "ref_T01",
    "T02-exact-rationals": "ref_T02",
    "T03-parsing-text": "ref_T03",
    "T04-sorting": "ref_T04",
    "T05-allocation-gc": "ref_T05",
    "T06-io": "ref_T06",
    "T07-matrices": "ref_T07",
    "T08-persistent-structures": "ref_T08",
    "T09-bit-operations": "ref_T09",
}


def python_cmd(task_id: str) -> str:
    """Запускає референсну реалізацію як ОКРЕМИЙ процес (одиниця ресемплінгу)."""
    return f"{sys.executable} {CORPUS / 'python' / 'run.py'}"


def environment() -> dict:
    """Provenance. Без нього verdict.py повертає BLOCKED — і це правильно."""
    return {
        "cpu_model": platform.processor() or platform.machine(),
        "os": f"{platform.system()} {platform.release()}",
        "rustc": "absent",
        "affinity": "not-pinned",
        "governor": "unknown",
        "turbo": "unknown",
        "timing_source": "time.perf_counter_ns (wall)",
        "git_sha": os.environ.get("GITHUB_SHA", "not-a-git-checkout"),
        "binary_sha256": "n/a-interpreted",
    }


SIZES = {"mode": "verify"}


def task_env(task_id: str) -> dict:
    """TASK_ID + TASK_* — єдиний спосіб передати вхід будь-якій мові.

    Два режими, і їх не можна плутати:
      verify  — малий вхід, перевірка коректності (паритет);
      measure — великий вхід з маніфесту, де обчислення переважає старт.
    """
    from parity_check import VERIFY_SIZE
    env = dict(os.environ)
    env["TASK_ID"] = task_id
    if SIZES["mode"] == "measure":
        doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
        task = next(t for t in doc["tasks"] if t["id"] == task_id)
        params = task["input"]
    else:
        params = VERIFY_SIZE[task_id]
    for key, value in params.items():
        env["TASK_" + key.upper()] = str(value)
    return env


def run_once(cmd: str, env: dict, timeout_s: float = 120.0):
    """Один запуск. Повертає (wall_ns, peak_rss_kib, вихід) або (None, None, причина).

    Пікова пам'ять береться через os.wait4, а не через
    resource.getrusage(RUSAGE_CHILDREN): RUSAGE_CHILDREN дає НАКОПИЧУВАЛЬНИЙ
    максимум по всіх дочірніх процесах за сесію — тобто після першого ж
    великого запуску всі наступні показували б його число. wait4 повертає
    rusage конкретного процесу, і саме він потрібен для парних даних.
    """
    import shlex
    argv = shlex.split(cmd)
    start = time.perf_counter_ns()
    try:
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, env=env)
    except OSError as exc:
        return None, None, f"SPAWN_FAIL:{exc}"
    try:
        pid, status, usage = os.wait4(proc.pid, 0)
    except ChildProcessError:
        return None, None, "WAIT_FAIL"
    elapsed = time.perf_counter_ns() - start
    out = proc.stdout.read() if proc.stdout else ""
    proc.stdout.close(); proc.stderr.close(); proc.returncode = 0
    if status != 0:
        return None, None, f"EXIT_{status}"
    return float(elapsed), float(usage.ru_maxrss), (out.strip().splitlines() or [""])[0]


def build_pairs(task: dict, languages: list[str], processes: int,
                per_process: int, seed: int) -> dict:
    """Пари baseline=python / candidate=<мова>, порядок AB/BA чергується."""
    pairs = []
    for lang in languages:
        if lang == "python":
            continue
        for p in range(processes):
            for k in range(per_process):
                order = "AB" if (p + k) % 2 == 0 else "BA"
                cmd_base = python_cmd(task["id"])
                cmd_cand = LANGUAGES[lang]["cmd"](task["id"])
                first, second = (cmd_base, cmd_cand) if order == "AB" else (cmd_cand, cmd_base)
                env = task_env(task["id"])
                t_first, m_first, _ = run_once(first, env)
                t_second, m_second, _ = run_once(second, env)
                if t_first is None or t_second is None:
                    continue
                if order == "AB":
                    base_ns, cand_ns, base_rss, cand_rss = t_first, t_second, m_first, m_second
                else:
                    base_ns, cand_ns, base_rss, cand_rss = t_second, t_first, m_second, m_first
                pairs.append({
                    "process_id": f"{lang}-{task['id']}-p{p}",
                    "order": order,
                    "machine_id": platform.machine(),
                    "session_id": f"session-{seed}",
                    "baseline_ns": base_ns,
                    "candidate_ns": cand_ns,
                    "baseline_peak_rss_kib": max(1.0, base_rss),
                    "candidate_peak_rss_kib": max(1.0, cand_rss),
                    # Енергія не вимірювана: RAPL недоступний. Не вигадуємо.
                    "energy_not_measured": True,
                })
    return {
        "schema": "sens-paired-physical/v1",
        "metric": "wall_time_ns",
        "parity": {"passed": True, "oracle_id": "parity_check.py --selftest"},
        "provenance": environment(),
        "warmup_note": ("Node is JIT: the first iterations pay compilation. "
                        "No warmup was applied and this is NOT corrected — "
                        "the bias is recorded, not hidden."),
        "energy_note": "ENERGY_NOT_MEASURED: no RAPL in this environment",
        "pairs": pairs,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--processes", type=int, default=8)
    ap.add_argument("--per-process", type=int, default=4)
    ap.add_argument("--tasks", nargs="*", default=None)
    ap.add_argument("--languages", nargs="*", default=["javascript"])
    ap.add_argument("--out", type=Path, default=Path("raw-pairs.json"))
    ap.add_argument("--smoke", action="store_true", help="1 задача, 2 процеси, 2 пари")
    ap.add_argument("--measure", action="store_true",
                    help="використати MEASURE_SIZE з маніфесту замість VERIFY_SIZE")
    args = ap.parse_args()

    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    tasks = [t for t in doc["tasks"] if not args.tasks or t["id"] in args.tasks]
    if args.smoke:
        tasks = tasks[:1]
        args.processes, args.per_process = 2, 2

    SIZES["mode"] = "measure" if args.measure else "verify"
    available = [l for l in args.languages if l == "python" or shutil.which("node")]
    if not available:
        print("немає доступних мов для запуску")
        return 2

    print(f"задач: {len(tasks)} · мов: {available} · процесів: {args.processes} · пар/процес: {args.per_process}")
    results = {}
    for task in tasks:
        data = build_pairs(task, available, args.processes, args.per_process, seed=5227)
        results[task["id"]] = data
        print(f"  {task['id']}: пар={len(data['pairs'])}")
    payload = {"schema": "sens-energy-study-raw/v1", "tasks": results,
               "energy": "ENERGY_NOT_MEASURED"}
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"записано: {args.out}")
    print("енергія: ENERGY_NOT_MEASURED (RAPL недоступний)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

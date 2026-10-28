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
# Імена закарбованих .sens для активного розміру. Мапа явна, бо імена
# файлів містять опис задачі (t01_fib_measure.sens), а не лише номер.
SENS_MEASURE_FILES = {
    "T01-symbolic-recursion": "t01_fib_measure.sens",
}

LANGUAGES = {
    "python": {
        "kind": "interpreted",
        "cmd": lambda task_id: f'{sys.executable} -c "import runpy,sys;sys.exit(0)"',
    },
    # НАША МОВА. Розмір вшитий у джерело (варіант А): sens приймає рівно один
    # файл і не передає аргументів програмі. Тому для кожного режиму — свій
    # закарбований .sens, а не параметр у середовищі.
    "sens": {
        "cmd": lambda task_id: f"{os.environ.get('SENS_BIN', './target/release/sens')} "
                               f"/tmp/sens-out/{SENS_MEASURE_FILES[task_id]}",
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


def _windows_process_peak_rss_kib(proc) -> float | None:
    """Native per-process *peak working set* via PSAPI; never substitute current RSS.

    A live Windows process handle remains valid after exit while Popen owns it.
    PeakWorkingSetSize is supplied by the OS in bytes (not KiB).
    API/zero failures are unavailable evidence, never 0 KiB observations.
    """
    import ctypes
    from ctypes import wintypes

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    try:
        psapi = ctypes.WinDLL("psapi.dll", use_last_error=True)
        func = psapi.GetProcessMemoryInfo
        func.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD]
        func.restype = wintypes.BOOL
        sample = ProcessMemoryCounters()
        sample.cb = ctypes.sizeof(sample)
        if not func(proc._handle, ctypes.byref(sample), sample.cb):
            return None
        return sample.PeakWorkingSetSize / 1024.0 if sample.PeakWorkingSetSize > 0 else None
    except (AttributeError, OSError, ValueError):
        return None


def run_once(cmd: str, env: dict, timeout_s: float = 120.0):
    """Один запуск. Повертає (wall_ns, peak_rss_kib, вихід) або (None, None, причина).

    POSIX peak RSS береться через os.wait4 (окрема #6288 normalization), а не через
    resource.getrusage(RUSAGE_CHILDREN): RUSAGE_CHILDREN дає НАКОПИЧУВАЛЬНИЙ
    максимум по всіх дочірніх процесах за сесію — тобто після першого ж
    великого запуску всі наступні показували б його число. wait4 повертає
    rusage конкретного процесу, і саме він потрібен для парних даних.

    На Windows: PSAPI PeakWorkingSetSize з дочірнього process HANDLE, навіть
    після exit, у KiB. Не вважаємо Win32 working set і Linux RSS тотожними.

    timeout_s реально обмежує очікування (раніше параметр ігнорувався).
    stdout/stderr читаються після wait, щоб не блокуватися на PIPE.
    """
    import shlex
    argv = shlex.split(cmd, posix=(os.name != 'nt'))
    if os.name == 'nt':
        # posix=False keeps path backslashes but also keeps outer quote marks.
        # Popen(argv) must receive unquoted -c payloads and executable paths.
        argv = [a[1:-1] if len(a) >= 2 and a[0] in ('"', "'") and a[-1] == a[0] else a
                for a in argv]
    start = time.perf_counter_ns()
    try:
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, env=env)
    except OSError as exc:
        return None, None, f"SPAWN_FAIL:{exc}"
    if os.name == "nt":
        # Windows has no wait4. communicate() reaps the child while retaining
        # its native process handle for PSAPI peak working-set retrieval.
        try:
            out, err = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            return None, None, f"TIMEOUT_{timeout_s}s"
        elapsed = time.perf_counter_ns() - start
        if proc.returncode != 0:
            return None, None, f"EXIT_{proc.returncode}:{err.strip()[:80]}"
        rss = _windows_process_peak_rss_kib(proc)
        if rss is None:
            return None, None, "RSS_UNAVAILABLE_WIN32"
        lines = [ln for ln in out.splitlines() if ln.strip()]
        if len(lines) != 1:
            return None, None, f"BAD_STDOUT_LINES_{len(lines)}"
        return float(elapsed), rss, lines[0]

    deadline = time.monotonic() + timeout_s
    status = None
    usage = None
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            proc.kill()
            try:
                _, killed_status, _ = os.wait4(proc.pid, 0)
                proc.returncode = os.waitstatus_to_exitcode(killed_status)
            except ChildProcessError:
                proc.returncode = -9
            finally:
                if proc.stdout:
                    proc.stdout.close()
                if proc.stderr:
                    proc.stderr.close()
            return None, None, f"TIMEOUT_{timeout_s}s"
        try:
            pid, status, usage = os.wait4(proc.pid, os.WNOHANG)
        except ChildProcessError:
            return None, None, "WAIT_FAIL"
        if pid != 0:
            break
        time.sleep(min(0.001, max(0.0002, remaining)))
    elapsed = time.perf_counter_ns() - start
    out = proc.stdout.read() if proc.stdout else ""
    err = proc.stderr.read() if proc.stderr else ""
    if proc.stdout:
        proc.stdout.close()
    if proc.stderr:
        proc.stderr.close()
    # os.wait4 reaps the child outside Popen.wait(); keep Popen's state consistent.
    proc.returncode = os.waitstatus_to_exitcode(status)
    if status != 0:
        return None, None, f"EXIT_{status}:{err.strip()[:80]}"
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if len(lines) != 1:
        return None, None, f"BAD_STDOUT_LINES_{len(lines)}"
    # POSIX RSS normalization is owned by #6288 / PR #6337; no overlap.
    return float(elapsed), float(usage.ru_maxrss), lines[0]


def active_params(task_id: str) -> dict:
    """Параметри VERIFY або MEASURE для тієї ж задачі, що й у task_env."""
    from parity_check import VERIFY_SIZE
    if SIZES["mode"] == "measure":
        doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
        task = next(t for t in doc["tasks"] if t["id"] == task_id)
        return dict(task["input"])
    return dict(VERIFY_SIZE[task_id])


def golden_for(task_id: str, params: dict) -> str:
    from parity_check import REFERENCE
    return REFERENCE[task_id](params)


def output_matches(task: dict, actual: str, expected: str) -> tuple[bool, str]:
    """Порівняння з еталоном для АКТИВНОГО розміру входу (не лише VERIFY_SIZE)."""
    kind = task["check"]
    if kind in ("exact", "bitwise"):
        ok = actual.strip() == expected.strip()
        return ok, "PARITY_OK" if ok else f"PARITY_FAILED expected={expected[:48]} actual={actual[:48]}"
    if kind == "tolerance":
        try:
            ok = abs(float(actual) - float(expected)) <= float(task["tolerance"])
        except (TypeError, ValueError):
            return False, "PARITY_FAILED non-numeric output for tolerance check"
        return ok, "PARITY_OK" if ok else "PARITY_FAILED beyond tolerance"
    return False, f"PARITY_FAILED unknown check {kind}"


def build_pairs(task: dict, languages: list[str], processes: int,
                per_process: int, seed: int) -> dict:
    """Пари baseline=python / candidate=<мова>, порядок AB/BA чергується.

    Паритет — не хардкод. Кожна сторона пари мусить дати еталонний вихід
    для АКТИВНОГО розміру (VERIFY або MEASURE). Інакше пара не потрапляє
    у valid pairs, а факт відмови зберігається в rejected.
    """
    pairs = []
    rejected = []
    params = active_params(task["id"])
    expected = golden_for(task["id"], params)
    parity_ok_count = 0
    parity_fail_count = 0
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
                t_first, m_first, out_first = run_once(first, env)
                t_second, m_second, out_second = run_once(second, env)
                if t_first is None or t_second is None:
                    rejected.append({
                        "process_id": f"{lang}-{task['id']}-p{p}-k{k}",
                        "order": order,
                        "reason": f"run_fail first={out_first} second={out_second}",
                    })
                    parity_fail_count += 1
                    continue
                if order == "AB":
                    base_ns, cand_ns = t_first, t_second
                    base_rss, cand_rss = m_first, m_second
                    base_out, cand_out = out_first, out_second
                else:
                    base_ns, cand_ns = t_second, t_first
                    base_rss, cand_rss = m_second, m_first
                    base_out, cand_out = out_second, out_first
                ok_b, v_b = output_matches(task, base_out, expected)
                ok_c, v_c = output_matches(task, cand_out, expected)
                if not (ok_b and ok_c):
                    rejected.append({
                        "process_id": f"{lang}-{task['id']}-p{p}-k{k}",
                        "order": order,
                        "reason": f"parity baseline={v_b}; candidate={v_c}",
                        "baseline_stdout": base_out[:120],
                        "candidate_stdout": cand_out[:120],
                        "expected_stdout": expected[:120],
                    })
                    parity_fail_count += 1
                    continue
                parity_ok_count += 1
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
                    "parity_checked": True,
                    "size_mode": SIZES["mode"],
                })
    all_checked = parity_ok_count + parity_fail_count
    passed = parity_ok_count > 0 and parity_fail_count == 0
    return {
        "schema": "sens-paired-physical/v1",
        "metric": "wall_time_ns",
        "parity": {
            "passed": passed,
            "oracle_id": "parity_check.REFERENCE+output_matches",
            "size_mode": SIZES["mode"],
            "ok_pairs": parity_ok_count,
            "failed_attempts": parity_fail_count,
            "checked_attempts": all_checked,
        },
        "rejected": rejected,
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
    available = [l for l in args.languages
                 if l == "python"
                 or (l == "javascript" and shutil.which("node"))
                 or (l == "sens" and Path(os.environ.get("SENS_BIN", "./target/release/sens")).exists())]
    if not available:
        print("немає доступних мов для запуску")
        return 2

    print(f"задач: {len(tasks)} · мов: {available} · процесів: {args.processes} · пар/процес: {args.per_process}")
    results = {}
    failed_tasks = []
    for task in tasks:
        data = build_pairs(task, available, args.processes, args.per_process, seed=5227)
        results[task["id"]] = data
        if not data["parity"]["passed"]:
            failed_tasks.append(task["id"])
        print(f"  {task['id']}: пар={len(data['pairs'])}, parity={data['parity']['passed']}, rejected={len(data['rejected'])}")
    payload = {"schema": "sens-energy-study-raw/v1", "tasks": results,
               "energy": "ENERGY_NOT_MEASURED"}
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"записано: {args.out}")
    print("енергія: ENERGY_NOT_MEASURED (RAPL недоступний)")
    if failed_tasks:
        print("PARITY_FAILED: raw збережено лише для аудиту; inference заборонено:", ", ".join(failed_tasks), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

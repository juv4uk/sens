#!/usr/bin/env python3
"""#1413 вісь A — об'єктивний бенчмарк поверхонь мови sens.

Одна й та сама програма генерується з ОДНОГО шаблону в чотири форми, що
відрізняються лише написанням примітивів:

  en    — англійські імена (def/lambda/cond/eq/+ ...)
  sens  — голі SENS-коди (00001011/00001000/...)
  uk    — українські імена (визначити/функція/за-умовою/тотожне?/додати ...)
  wrap  — англійські імена, але eq/atom/cons/car/cdr/+/- обгорнуті
          написаними Lisp-функціями (стиль більшості lib/*.lisp, #1277)

Імена користувацьких функцій (fib, loop, ...) однакові в усіх формах —
різниться лише поверхня примітивів.

Навантаження навмисно використовують лише eq/atom/cons/car/cdr/+/-:
на main 33bfb53a `(< 2 1)` повертає "0", який `cond` трактує як істину
(див. звіт), тож програми з `<`/`=` зараз дають неправильні відповіді.

Кожен прогін спершу перевіряє відповідь; неправильна відповідь = збій
бенчмарку, не число.

Запуск (середовище — лише Guix-профіль репозиторію, §9a):
  guix time-machine -C channels.scm -- shell -m manifest.scm \
      -m benchmarks/sens-surface/manifest.scm -- \
      python3 benchmarks/sens-surface/run.py --sens target-guix/release/sens
"""

import argparse
import datetime as dt
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Поверхні: токен шаблону -> написання в кожній формі.
# SENS-коди звірені з docs/generated/function-table.md.
SURFACES = {
    "def":    {"en": "def",    "sens": "00001011", "uk": "визначити", "wrap": "def"},
    "lambda": {"en": "lambda", "sens": "00001000", "uk": "функція",   "wrap": "lambda"},
    "cond":   {"en": "cond",   "sens": "00000111", "uk": "за-умовою", "wrap": "cond"},
    "quote":  {"en": "quote",  "sens": "00000001", "uk": "як-є",      "wrap": "quote"},
    "eq":     {"en": "eq",     "sens": "00000011", "uk": "тотожне?",  "wrap": "my-eq"},
    "atom":   {"en": "atom",   "sens": "00000010", "uk": "атом?",     "wrap": "my-atom"},
    "cons":   {"en": "cons",   "sens": "00000100", "uk": "сполучити", "wrap": "my-cons"},
    "car":    {"en": "car",    "sens": "00000101", "uk": "перше",     "wrap": "my-car"},
    "cdr":    {"en": "cdr",    "sens": "00000110", "uk": "решта",     "wrap": "my-cdr"},
    "+":      {"en": "+",      "sens": "00001100", "uk": "додати",    "wrap": "my-add"},
    "-":      {"en": "-",      "sens": "00001101", "uk": "відняти",   "wrap": "my-sub"},
}
ALL_FORMS = ["en", "sens", "uk", "wrap"]
FORMS = ["en", "sens"]  # за замовчуванням: англійський Lisp проти SENS

WRAP_PRELUDE = """\
(def my-eq (lambda (a b) (eq a b)))
(def my-atom (lambda (a) (atom a)))
(def my-cons (lambda (a b) (cons a b)))
(def my-car (lambda (a) (car a)))
(def my-cdr (lambda (a) (cdr a)))
(def my-add (lambda (a b) (+ a b)))
(def my-sub (lambda (a b) (- a b)))
"""

# ---------------------------------------------------------------------------
# Навантаження. {токен} замінюється на поверхню форми. {N}/{R} — параметри.
# expected(params) рахується незалежно в Python — це оракул правильності.


def fib_py(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


WORKLOADS = {
    # Дерево рекурсивних викликів: переважає вартість виклику функції.
    "fib": {
        "params": {"N": 25},
        "src": """\
({def} fib ({lambda} (n)
  ({cond} (({eq} n 0) 0)
        (({eq} n 1) 1)
        (t ({+} (fib ({-} n 1)) (fib ({-} n 2)))))))
(print (fib {N}))
""",
        "expected": lambda p: str(fib_py(p["N"])),
    },
    # Хвостовий цикл: арифметика + eq на кожному кроці.
    "loop": {
        "params": {"N": 300000},
        "src": """\
({def} loop ({lambda} (n acc)
  ({cond} (({eq} n 0) acc)
        (t (loop ({-} n 1) ({+} acc 2))))))
(print (loop {N} 0))
""",
        "expected": lambda p: str(2 * p["N"]),
    },
    # Списки: побудова cons-ами, розворот акумулятором, підрахунок довжини.
    "lists": {
        "params": {"N": 1000, "R": 120},
        "src": """\
({def} build ({lambda} (n acc)
  ({cond} (({eq} n 0) acc)
        (t (build ({-} n 1) ({cons} n acc))))))
({def} rev ({lambda} (xs acc)
  ({cond} (({atom} xs) acc)
        (t (rev ({cdr} xs) ({cons} ({car} xs) acc))))))
({def} len ({lambda} (xs n)
  ({cond} (({atom} xs) n)
        (t (len ({cdr} xs) ({+} n 1))))))
({def} work ({lambda} (r total)
  ({cond} (({eq} r 0) total)
        (t (work ({-} r 1) ({+} total (len (rev (build {N} ({quote} ())) ({quote} ())) 0)))))))
(print (work {R} 0))
""",
        "expected": lambda p: str(p["N"] * p["R"]),
    },
    # Пошук eq у списку (форма реального member?, #1278), найгірший випадок.
    "member": {
        "params": {"N": 100, "R": 5000},
        "src": """\
({def} build ({lambda} (n acc)
  ({cond} (({eq} n 0) acc)
        (t (build ({-} n 1) ({cons} n acc))))))
({def} mem ({lambda} (x xs)
  ({cond} (({atom} xs) 0)
        (({eq} x ({car} xs)) 1)
        (t (mem x ({cdr} xs))))))
({def} xs (build {N} ({quote} ())))
({def} work ({lambda} (r hits)
  ({cond} (({eq} r 0) hits)
        (t (work ({-} r 1) ({+} hits (mem {N} xs)))))))
(print (work {R} 0))
""",
        "expected": lambda p: str(p["R"]),
    },
    # Замикання: створення і виклик lambda з захопленою змінною.
    "closures": {
        "params": {"N": 200000},
        "src": """\
({def} make-adder ({lambda} (k) ({lambda} (x) ({+} x k))))
({def} add3 (make-adder 3))
({def} loop ({lambda} (n acc)
  ({cond} (({eq} n 0) acc)
        (t (loop ({-} n 1) (add3 acc))))))
(print (loop {N} 0))
""",
        "expected": lambda p: str(3 * p["N"]),
    },
}

EMPTY_SRC = "(print 0)\n"


def render(template, form, params):
    out = template
    for key, value in params.items():
        out = out.replace("{" + key + "}", str(value))
    # Довші токени першими, щоб {cdr}/{car} не зачепили одне одного.
    for token in sorted(SURFACES, key=len, reverse=True):
        out = out.replace("{" + token + "}", SURFACES[token][form])
    if "{" in out:
        raise ValueError(f"незамінений токен у формі {form}: {out}")
    if form == "wrap":
        out = WRAP_PRELUDE + out
    return out


# ---------------------------------------------------------------------------


def run_once(sens, path, cpu):
    cmd = [sens, str(path)]
    if cpu is not None:
        cmd = ["taskset", "-c", str(cpu)] + cmd
    load1 = os.getloadavg()[0]
    started = time.perf_counter()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, status, rusage = os.wait4(proc.pid, 0)
    wall = time.perf_counter() - started
    stdout = proc.stdout.read().decode("utf-8", "replace")
    stderr = proc.stderr.read().decode("utf-8", "replace")
    proc.stdout.close()
    proc.stderr.close()
    return {
        "wall_s": wall,
        "user_s": rusage.ru_utime,
        "sys_s": rusage.ru_stime,
        "maxrss_kb": rusage.ru_maxrss,
        "exit": os.waitstatus_to_exitcode(status),
        "load1": load1,
        "stdout": stdout,
        "stderr": stderr,
    }


def answer_of(stdout):
    """Остання непорожня лінія stdout — надрукована відповідь."""
    lines = [l.strip() for l in stdout.splitlines() if l.strip()]
    return lines[-1] if lines else ""


def median(xs):
    return statistics.median(xs)


def env_facts(sens, repo):
    def sh(cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True,
                                  cwd=repo, timeout=30).stdout.strip()
        except Exception as exc:  # noqa: BLE001 — факт середовища, не логіка
            return f"unknown ({exc})"

    cpu = "unknown"
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    return {
        "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "git_sha": sh(["git", "rev-parse", "HEAD"]),
        "git_dirty": sh(["git", "status", "--porcelain", "--untracked-files=no"]) != "",
        "sens_binary": str(Path(sens).resolve()),
        "sens_sha256": sh(["sha256sum", str(Path(sens).resolve())]).split(" ")[0],
        "rustc": sh(["rustc", "--version"]),
        "guix_environment": os.environ.get("GUIX_ENVIRONMENT", "not-set"),
        "python": platform.python_version(),
        "kernel": platform.release(),
        "cpu": cpu,
        "nproc": os.cpu_count(),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sens", required=True, help="шлях до бінарника sens")
    ap.add_argument("--samples", type=int, default=7)
    ap.add_argument("--warmup", type=int, default=1)
    ap.add_argument("--cpu", type=int, default=None, help="taskset -c CPU (опційно)")
    ap.add_argument("--only", default=None, help="кома-список навантажень")
    ap.add_argument("--check-only", action="store_true",
                    help="лише перевірити правильність усіх форм, без замірів")
    ap.add_argument("--out", default=None, help="каталог результатів")
    ap.add_argument("--forms", default="en,sens",
                    help="кома-список форм з en,sens,uk,wrap (за замовч. en,sens)")
    args = ap.parse_args()
    global FORMS
    FORMS = [f for f in args.forms.split(",") if f in ALL_FORMS]

    repo = Path(__file__).resolve().parents[2]
    names = args.only.split(",") if args.only else list(WORKLOADS)
    workdir = Path(tempfile.mkdtemp(prefix="sens-bench-"))

    programs = {}  # (workload, form) -> path
    for name in names:
        wl = WORKLOADS[name]
        for form in FORMS:
            path = workdir / f"{name}-{form}.lisp"
            path.write_text(render(wl["src"], form, wl["params"]), encoding="utf-8")
            programs[(name, form)] = path
    empty = workdir / "empty.lisp"
    empty.write_text(EMPTY_SRC, encoding="utf-8")

    # 1. Правильність — до будь-якого заміру часу.
    failures = []
    for name in names:
        expected = WORKLOADS[name]["expected"](WORKLOADS[name]["params"])
        for form in FORMS:
            r = run_once(args.sens, programs[(name, form)], args.cpu)
            got = answer_of(r["stdout"])
            ok = r["exit"] == 0 and got == expected
            print(f"[check] {name:9s} {form:5s} expected={expected} got={got!r} "
                  f"exit={r['exit']} wall={r['wall_s']:.2f}s {'OK' if ok else 'FAIL'}",
                  flush=True)
            if not ok:
                failures.append((name, form, expected, got, r["stderr"][:400]))
    if failures:
        print("\nПРАВИЛЬНІСТЬ НЕ ПІДТВЕРДЖЕНА — заміри часу не виконуються:")
        for f in failures:
            print("  ", f)
        sys.exit(2)
    if args.check_only:
        print("усі форми дають правильні відповіді")
        return

    # 2. Заміри. Порядок форм обертається в кожному раунді (A/B/C/D,
    #    B/C/D/A, ...), щоб дрейф навантаження машини не падав на одну форму.
    runs = []
    total_rounds = args.warmup + args.samples
    for rnd in range(total_rounds):
        warm = rnd < args.warmup
        order = FORMS[rnd % len(FORMS):] + FORMS[:rnd % len(FORMS)]
        r = run_once(args.sens, empty, args.cpu)
        runs.append({"round": rnd, "warmup": warm, "workload": "empty",
                     "form": "-", **{k: v for k, v in r.items()
                                     if k not in ("stdout", "stderr")}})
        for name in names:
            for form in order:
                r = run_once(args.sens, programs[(name, form)], args.cpu)
                expected = WORKLOADS[name]["expected"](WORKLOADS[name]["params"])
                if answer_of(r["stdout"]) != expected or r["exit"] != 0:
                    print(f"ПОМИЛКА в раунді {rnd}: {name}/{form}", r["stderr"][:300])
                    sys.exit(3)
                runs.append({"round": rnd, "warmup": warm, "workload": name,
                             "form": form, **{k: v for k, v in r.items()
                                              if k not in ("stdout", "stderr")}})
        print(f"[round {rnd + 1}/{total_rounds}{' warmup' if warm else ''}] "
              f"load1={os.getloadavg()[0]:.2f}", flush=True)

    measured = [r for r in runs if not r["warmup"]]
    startup = [r["wall_s"] for r in measured if r["workload"] == "empty"]
    startup_med = median(startup)

    summary = {"startup_s": {"median": startup_med, "min": min(startup),
                             "max": max(startup)},
               "workloads": {}}
    for name in names:
        per_form = {}
        for form in FORMS:
            walls = [r["wall_s"] for r in measured
                     if r["workload"] == name and r["form"] == form]
            cpu = [r["user_s"] + r["sys_s"] for r in measured
                   if r["workload"] == name and r["form"] == form]
            per_form[form] = {
                "wall_median": median(walls), "wall_min": min(walls),
                "wall_max": max(walls),
                "compute_median": median(walls) - startup_med,
                "cpu_median": median(cpu),
                "maxrss_kb_max": max(r["maxrss_kb"] for r in measured
                                     if r["workload"] == name and r["form"] == form),
            }
        # Парні співвідношення в межах одного раунду (обчислення без старту).
        ratios = {}
        for form in FORMS:
            vals = []
            for rnd in sorted({r["round"] for r in measured}):
                def pick(f):
                    return next(r["wall_s"] for r in measured if r["round"] == rnd
                                and r["workload"] == name and r["form"] == f)
                st = next(r["wall_s"] for r in measured if r["round"] == rnd
                          and r["workload"] == "empty")
                base = pick("sens") - st
                if base > 0:
                    vals.append((pick(form) - st) / base)
            ratios[form] = {"median": median(vals), "min": min(vals),
                            "max": max(vals)} if vals else None
        summary["workloads"][name] = {"params": WORKLOADS[name]["params"],
                                      "forms": per_form, "ratio_vs_sens": ratios}

    facts = env_facts(args.sens, repo)
    facts["samples"] = args.samples
    facts["warmup"] = args.warmup
    facts["cpu_pin"] = args.cpu
    facts["load1_range"] = [min(r["load1"] for r in measured),
                            max(r["load1"] for r in measured)]

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = Path(args.out) if args.out else (
        repo / "benchmarks" / "sens-surface" / "results"
        / f"{stamp}-{facts['git_sha'][:8]}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "env.json").write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    cols = ["round", "warmup", "workload", "form", "wall_s", "user_s", "sys_s",
            "maxrss_kb", "exit", "load1"]
    with open(out / "runs.tsv", "w", encoding="utf-8") as fh:
        fh.write("\t".join(cols) + "\n")
        for r in runs:
            fh.write("\t".join(str(r[c]) for c in cols) + "\n")
    for (name, form), path in programs.items():
        (out / "programs").mkdir(exist_ok=True)
        (out / "programs" / path.name).write_text(path.read_text(encoding="utf-8"),
                                                  encoding="utf-8")

    # Короткий звіт українською в stdout.
    print(f"\nРезультати: {out}")
    print(f"sha={facts['git_sha'][:8]} rustc={facts['rustc']} guix={facts['guix_environment']}")
    print(f"старт (порожня програма): медіана {startup_med:.3f}s "
          f"[{min(startup):.3f}–{max(startup):.3f}]; load1 {facts['load1_range']}")
    print(f"{'навантаження':10s} {'форма':5s} {'wall мед.':>9s} {'обчисл.':>8s} "
          f"{'min–max':>15s} {'/sens (мед. [min–max])':>24s}")
    for name in names:
        s = summary["workloads"][name]
        for form in FORMS:
            f = s["forms"][form]
            r = s["ratio_vs_sens"][form]
            rs = f"{r['median']:.3f} [{r['min']:.3f}–{r['max']:.3f}]" if r else "n/a"
            print(f"{name:10s} {form:5s} {f['wall_median']:9.3f} {f['compute_median']:8.3f} "
                  f"{f['wall_min']:7.3f}–{f['wall_max']:<7.3f} {rs:>24s}")


if __name__ == "__main__":
    main()

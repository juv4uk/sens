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

Навантаження навмисно використовують лише eq/atom/cons/car/cdr/+/-.
Після Predicate1 reset (#1703/#1663) кожна умова COND є двочастинною:
предикат напряму повертає точний one-bit результат, без T/NIL truthiness
і без expected-result поля.

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
    "def":    {"en": "def",    "sens": "00001011", "uk": "визначити", "wrap": "def", "legacy-en": "def"},
    "lambda": {"en": "lambda", "sens": "00001000", "uk": "функція",   "wrap": "lambda", "legacy-en": "lambda"},
    "cond":   {"en": "cond",   "sens": "00000111", "uk": "за-умовою", "wrap": "cond", "legacy-en": "cond"},
    "quote":  {"en": "quote",  "sens": "00000001", "uk": "як-є",      "wrap": "quote", "legacy-en": "quote"},
    "eq":     {"en": "eq?",     "sens": "00000011", "uk": "тотожне?",  "wrap": "my-eq", "legacy-en": "eq"},
    "atom":   {"en": "atom?",   "sens": "00000010", "uk": "атом?",     "wrap": "my-atom", "legacy-en": "atom"},
    "cons":   {"en": "cons",   "sens": "00000100", "uk": "сполучити", "wrap": "my-cons", "legacy-en": "cons"},
    "car":    {"en": "car",    "sens": "00000101", "uk": "перше",     "wrap": "my-car", "legacy-en": "car"},
    "cdr":    {"en": "cdr",    "sens": "00000110", "uk": "решта",     "wrap": "my-cdr", "legacy-en": "cdr"},
    "+":      {"en": "+",      "sens": "00001100", "uk": "додати",    "wrap": "my-add", "legacy-en": "+"},
    "-":      {"en": "-",      "sens": "00001101", "uk": "відняти",   "wrap": "my-sub", "legacy-en": "-"},
}
ALL_FORMS = ["en", "sens", "uk", "wrap", "legacy-en"]
FORMS = ["en", "sens"]  # за замовчуванням: англійський Lisp проти SENS

WRAP_PRELUDE = """\
(def my-eq (lambda (a b) (eq? a b)))
(def my-atom (lambda (a) (atom? a)))
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


def ack_py(m, n):
    # Ітеративний Аккерман через стек — незалежний від рекурсії оракул.
    stack = [m]
    while stack:
        m = stack.pop()
        if m == 0:
            n += 1
        elif n == 0:
            stack.append(m - 1)
            n = 1
        else:
            stack.append(m - 1)
            stack.append(m)
            n -= 1
    return n


BUILD = """\
({def} build ({lambda} (n acc)
  ({cond} (({eq} n 0) acc)
        (({eq} 0 0) (build ({-} n 1) ({cons} n acc))))))
"""
LEN = """\
({def} len ({lambda} (xs n)
  ({cond} (({atom} xs) n)
        (({eq} 0 0) (len ({cdr} xs) ({+} n 1))))))
"""
TREE = """\
({def} mk ({lambda} (d)
  ({cond} (({eq} d 0) ({quote} leaf))
        (({eq} 0 0) ({cons} (mk ({-} d 1)) (mk ({-} d 1)))))))
"""

# Кожне навантаження: setup (визначення), call (вираз-відповідь),
# params (повний розмір), small (для valgrind), expected (оракул).
WORKLOADS = {
    # Дерево рекурсивних викликів: переважає вартість виклику функції.
    "fib": {
        "params": {"N": 25}, "small": {"N": 16},
        "setup": """\
({def} fib ({lambda} (n)
  ({cond} (({eq} n 0) 0)
        (({eq} n 1) 1)
        (({eq} 0 0) ({+} (fib ({-} n 1)) (fib ({-} n 2)))))))
""",
        "call": "(fib {N})",
        "expected": lambda p: str(fib_py(p["N"])),
    },
    # Хвостовий цикл: арифметика + eq на кожному кроці.
    "loop": {
        "params": {"N": 300000}, "small": {"N": 5000},
        "setup": """\
({def} loop ({lambda} (n acc)
  ({cond} (({eq} n 0) acc)
        (({eq} 0 0) (loop ({-} n 1) ({+} acc 2))))))
""",
        "call": "(loop {N} 0)",
        "expected": lambda p: str(2 * p["N"]),
    },
    # Списки: побудова cons-ами, розворот акумулятором, підрахунок довжини.
    "lists": {
        "params": {"N": 1000, "R": 120}, "small": {"N": 200, "R": 10},
        "setup": BUILD + LEN + """\
({def} rev ({lambda} (xs acc)
  ({cond} (({atom} xs) acc)
        (({eq} 0 0) (rev ({cdr} xs) ({cons} ({car} xs) acc))))))
({def} work ({lambda} (r total)
  ({cond} (({eq} r 0) total)
        (({eq} 0 0) (work ({-} r 1) ({+} total (len (rev (build {N} ({quote} ())) ({quote} ())) 0)))))))
""",
        "call": "(work {R} 0)",
        "expected": lambda p: str(p["N"] * p["R"]),
    },
    # Пошук eq у списку (форма реального member?, #1278), найгірший випадок.
    "member": {
        "params": {"N": 100, "R": 5000}, "small": {"N": 100, "R": 50},
        "setup": BUILD + """\
({def} mem ({lambda} (x xs)
  ({cond} (({atom} xs) 0)
        (({eq} x ({car} xs)) 1)
        (({eq} 0 0) (mem x ({cdr} xs))))))
({def} xs (build {N} ({quote} ())))
({def} work ({lambda} (r hits)
  ({cond} (({eq} r 0) hits)
        (({eq} 0 0) (work ({-} r 1) ({+} hits (mem {N} xs)))))))
""",
        "call": "(work {R} 0)",
        "expected": lambda p: str(p["R"]),
    },
    # Замикання: створення і виклик lambda з захопленою змінною.
    "closures": {
        "params": {"N": 200000}, "small": {"N": 5000},
        "setup": """\
({def} make-adder ({lambda} (k) ({lambda} (x) ({+} x k))))
({def} add3 (make-adder 3))
({def} loop ({lambda} (n acc)
  ({cond} (({eq} n 0) acc)
        (({eq} 0 0) (loop ({-} n 1) (add3 acc))))))
""",
        "call": "(loop {N} 0)",
        "expected": lambda p: str(3 * p["N"]),
    },
    # Аккерман: глибока не-хвостова рекурсія з вкладеним викликом.
    "ackermann": {
        "params": {"N": 7}, "small": {"N": 3},
        "setup": """\
({def} ack ({lambda} (m n)
  ({cond} (({eq} m 0) ({+} n 1))
        (({eq} n 0) (ack ({-} m 1) 1))
        (({eq} 0 0) (ack ({-} m 1) (ack m ({-} n 1)))))))
""",
        "call": "(ack 3 {N})",
        "expected": lambda p: str(ack_py(3, p["N"])),
    },
    # Бінарне дерево: алокація пар і обхід обох гілок.
    "tree": {
        "params": {"N": 16}, "small": {"N": 10},
        "setup": TREE + """\
({def} cnt ({lambda} (x)
  ({cond} (({atom} x) 1)
        (({eq} 0 0) ({+} (cnt ({car} x)) (cnt ({cdr} x)))))))
""",
        "call": "(cnt (mk {N}))",
        "expected": lambda p: str(2 ** p["N"]),
    },
    # Асоціативний список: пошук за ключем eq, O(N^2).
    "assoc": {
        "params": {"N": 400}, "small": {"N": 30},
        "setup": """\
({def} mkal ({lambda} (n acc)
  ({cond} (({eq} n 0) acc)
        (({eq} 0 0) (mkal ({-} n 1) ({cons} ({cons} n ({+} n n)) acc))))))
({def} look ({lambda} (k al)
  ({cond} (({atom} al) 0)
        (({eq} k ({car} ({car} al))) ({cdr} ({car} al)))
        (({eq} 0 0) (look k ({cdr} al))))))
({def} sumall ({lambda} (k al acc)
  ({cond} (({eq} k 0) acc)
        (({eq} 0 0) (sumall ({-} k 1) al ({+} acc (look k al)))))))
""",
        "call": "(sumall {N} (mkal {N} ({quote} ())) 0)",
        "expected": lambda p: str(p["N"] * (p["N"] + 1)),
    },
    # Функції вищого порядку: map/fold з анонімними lambda.
    "mapfold": {
        "params": {"N": 1000, "R": 60}, "small": {"N": 200, "R": 5},
        "setup": BUILD + """\
({def} mymap ({lambda} (f xs)
  ({cond} (({atom} xs) xs)
        (({eq} 0 0) ({cons} (f ({car} xs)) (mymap f ({cdr} xs)))))))
({def} myfold ({lambda} (f acc xs)
  ({cond} (({atom} xs) acc)
        (({eq} 0 0) (myfold f (f acc ({car} xs)) ({cdr} xs))))))
({def} work ({lambda} (r total)
  ({cond} (({eq} r 0) total)
        (({eq} 0 0) (work ({-} r 1)
                 ({+} total (myfold ({lambda} (a b) ({+} a b)) 0
                                   (mymap ({lambda} (x) ({+} x x)) (build {N} ({quote} ()))))))))))
""",
        "call": "(work {R} 0)",
        "expected": lambda p: str(p["R"] * p["N"] * (p["N"] + 1)),
    },
    # Взаємна рекурсія двох функцій.
    "evenodd": {
        "params": {"N": 300000}, "small": {"N": 5000},
        "setup": """\
({def} is-even ({lambda} (n)
  ({cond} (({eq} n 0) 1)
        (({eq} 0 0) (is-odd ({-} n 1))))))
({def} is-odd ({lambda} (n)
  ({cond} (({eq} n 0) 0)
        (({eq} 0 0) (is-even ({-} n 1))))))
""",
        "call": "(is-even {N})",
        "expected": lambda p: "1" if p["N"] % 2 == 0 else "0",
    },
    # Розгортання вкладеної структури в плаский список.
    "flatten": {
        "params": {"N": 15}, "small": {"N": 9},
        "setup": TREE + LEN + """\
({def} flat ({lambda} (x acc)
  ({cond} (({atom} x) ({cons} x acc))
        (({eq} 0 0) (flat ({car} x) (flat ({cdr} x) acc))))))
""",
        "call": "(len (flat (mk {N}) ({quote} ())) 0)",
        "expected": lambda p: str(2 ** p["N"]),
    },
}


def program_text(wl, params):
    return wl["setup"] + "(print " + wl["call"] + ")\n"


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


# ---------------------------------------------------------------------------
# #1586: іменований контекст навантаження машини. Правило зафіксовано явно,
# щоб споживач замірів (поріг вибору CPU/карта, #1568) не виводив поріг із
# замірів під робочим навантаженням без позначки: CPU-база з «хворої»
# машини — це налаштований на хвору машину поріг.
LOAD_CONTEXT_RULE = "idle: load1 < 0.25*nproc; high: інакше; unknown: nproc недоступний"


def load_context(load1, nproc):
    """Класифікує контекст навантаження за #1586. Названий стан, не мовчазне
    припущення: 'unknown' краще за фальшиве 'idle'."""
    if nproc is None or nproc <= 0:
        return "unknown"
    return "idle" if load1 < 0.25 * nproc else "high"


def params_str(params):
    """#1587: канонічний рядок розміру навантаження для кожного рядка звіту."""
    return ",".join(f"{k}={v}" for k, v in sorted(params.items()))


def run_once(sens, path, cpu):
    cmd = [sens, str(path)]
    if cpu is not None:
        cmd = ["taskset", "-c", str(cpu)] + cmd
    load1 = os.getloadavg()[0]
    ctx = load_context(load1, os.cpu_count())
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
        "load_context": ctx,
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
    ap.add_argument("--small", action="store_true",
                    help="малі розміри навантажень (для valgrind)")
    ap.add_argument("--emit", default=None,
                    help="лише записати setup/call/expected кожної форми в каталог і вийти")
    ap.add_argument("--forms", default="en,sens",
                    help="кома-список форм з en,sens,uk,wrap (за замовч. en,sens)")
    args = ap.parse_args()
    global FORMS
    FORMS = [f for f in args.forms.split(",") if f in ALL_FORMS]

    repo = Path(__file__).resolve().parents[2]
    names = args.only.split(",") if args.only else list(WORKLOADS)
    workdir = Path(tempfile.mkdtemp(prefix="sens-bench-"))

    if args.emit:
        emit = Path(args.emit)
        emit.mkdir(parents=True, exist_ok=True)
        # #1587: params.tsv — розмір кожного навантаження є частиною
        # випуску; споживачі (ci_bench.sh, майбутній GPU-3 #1567) не мають
        # права виводити рядок без розміру.
        param_rows = []
        for name in names:
            wl = WORKLOADS[name]
            params = wl["small"] if args.small else wl["params"]
            param_rows.append(f"{name}\t{params_str(params)}")
            for form in FORMS:
                (emit / f"{name}-{form}.setup.lisp").write_text(
                    render(wl["setup"], form, params), encoding="utf-8")
                (emit / f"{name}-{form}.call.lisp").write_text(
                    render(wl["call"], form, params) + "\n", encoding="utf-8")
            (emit / f"{name}.expected").write_text(wl["expected"](params) + "\n")
        (emit / "params.tsv").write_text("\n".join(param_rows) + "\n", encoding="utf-8")
        print(f"записано в {emit}")
        return

    programs = {}  # (workload, form) -> path
    for name in names:
        wl = WORKLOADS[name]
        params = wl["small"] if args.small else wl["params"]
        wl["active"] = params
        for form in FORMS:
            path = workdir / f"{name}-{form}.lisp"
            path.write_text(render(program_text(wl, params), form, params), encoding="utf-8")
            programs[(name, form)] = path
    empty = workdir / "empty.lisp"
    empty.write_text(EMPTY_SRC, encoding="utf-8")

    # 1. Правильність — до будь-якого заміру часу.
    failures = []
    for name in names:
        expected = WORKLOADS[name]["expected"](WORKLOADS[name]["active"])
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
                     "params": "-", "form": "-", **{k: v for k, v in r.items()
                                             if k not in ("stdout", "stderr")}})
        for name in names:
            for form in order:
                r = run_once(args.sens, programs[(name, form)], args.cpu)
                expected = WORKLOADS[name]["expected"](WORKLOADS[name]["active"])
                if answer_of(r["stdout"]) != expected or r["exit"] != 0:
                    print(f"ПОМИЛКА в раунді {rnd}: {name}/{form}", r["stderr"][:300])
                    sys.exit(3)
                runs.append({"round": rnd, "warmup": warm, "workload": name,
                             "params": params_str(WORKLOADS[name]["active"]),
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
        summary["workloads"][name] = {"params": WORKLOADS[name]["active"],
                                      "forms": per_form, "ratio_vs_sens": ratios}

    facts = env_facts(args.sens, repo)
    facts["samples"] = args.samples
    facts["warmup"] = args.warmup
    facts["cpu_pin"] = args.cpu
    facts["load1_range"] = [min(r["load1"] for r in measured),
                            max(r["load1"] for r in measured)]
    # #1586: названий контекст замірів; правило вище, у LOAD_CONTEXT_RULE.
    facts["load_context"] = load_context(
        statistics.median(r["load1"] for r in measured), os.cpu_count())
    facts["load_context_rule"] = LOAD_CONTEXT_RULE

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = Path(args.out) if args.out else (
        repo / "benchmarks" / "sens-surface" / "results"
        / f"{stamp}-{facts['git_sha'][:8]}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "env.json").write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    cols = ["round", "warmup", "workload", "params", "form", "wall_s", "user_s", "sys_s",
            "maxrss_kb", "exit", "load1", "load_context"]
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
    print(f"контекст навантаження: {facts['load_context']} "
          f"(правило: {facts['load_context_rule']})")
    print(f"{'навантаження':10s} {'параметри':18s} {'форма':5s} {'wall мед.':>9s} {'обчисл.':>8s} "
          f"{'min–max':>15s} {'/sens (мед. [min–max])':>24s}")
    for name in names:
        s = summary["workloads"][name]
        for form in FORMS:
            f = s["forms"][form]
            r = s["ratio_vs_sens"][form]
            rs = f"{r['median']:.3f} [{r['min']:.3f}–{r['max']:.3f}]" if r else "n/a"
            print(f"{name:10s} {params_str(s['params']):18s} {form:5s} {f['wall_median']:9.3f} {f['compute_median']:8.3f} "
                  f"{f['wall_min']:7.3f}–{f['wall_max']:<7.3f} {rs:>24s}")


if __name__ == "__main__":
    main()

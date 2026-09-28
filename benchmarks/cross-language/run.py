#!/usr/bin/env python3
"""#1546/#1547/#1548: SENS ↔ CPython ↔ Lua 5.4 ↔ Racket CS.

Це benchmark реалізацій, не рейтинг абстрактних мов. SENS-програми
генеруються з уже наявних шаблонів benchmarks/sens-surface/run.py;
зовнішні adapters реалізують ті самі алгоритми й параметри.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import math
import os
import platform
import re
import statistics
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import racket_adapter


ROOT = Path(__file__).resolve().parents[2]
SENS_SURFACE_RUN = ROOT / "benchmarks" / "sens-surface" / "run.py"
CPYTHON_DRIVER = ROOT / "benchmarks" / "cross-language" / "cpython_driver.py"
LUA_DRIVER = ROOT / "benchmarks" / "cross-language" / "lua_driver.lua"
RACKET_DRIVER = ROOT / "benchmarks" / "cross-language" / "racket_driver.rkt"
CASES = ("fib", "loop", "ackermann", "closures", "evenodd")

# Параметри спільні й достатньо малі для CPython-рекурсії під Cachegrind.
# Алгоритм не замінюється ітеративним лише заради Python.
PARAMS = {
    "fib": {"N": 16},
    "loop": {"N": 700},
    "ackermann": {"N": 3},
    "closures": {"N": 700},
    "evenodd": {"N": 700},
}


def load_sens_surface_module():
    spec = importlib.util.spec_from_file_location("sens_surface_bench", SENS_SURFACE_RUN)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"не вдалося завантажити {SENS_SURFACE_RUN}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def python_source(name: str, params: dict[str, int]) -> str:
    n = params["N"]
    limit = max(10_000, n * 4 + 100)

    if name == "fib":
        return f"""import sys
sys.setrecursionlimit({limit})

def fib(n):
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fib(n - 1) + fib(n - 2)

def bench():
    return fib({n})

if __name__ == "__main__":
    print(bench())
"""

    if name == "loop":
        return f"""import sys
sys.setrecursionlimit({limit})

def loop(n, acc):
    if n == 0:
        return acc
    return loop(n - 1, acc + 2)

def bench():
    return loop({n}, 0)

if __name__ == "__main__":
    print(bench())
"""

    if name == "ackermann":
        return f"""import sys
sys.setrecursionlimit({limit})

def ack(m, n):
    if m == 0:
        return n + 1
    if n == 0:
        return ack(m - 1, 1)
    return ack(m - 1, ack(m, n - 1))

def bench():
    return ack(3, {n})

if __name__ == "__main__":
    print(bench())
"""

    if name == "closures":
        return f"""import sys
sys.setrecursionlimit({limit})

def make_adder(k):
    def add(x):
        return x + k
    return add

add3 = make_adder(3)

def loop(n, acc):
    if n == 0:
        return acc
    return loop(n - 1, add3(acc))

def bench():
    return loop({n}, 0)

if __name__ == "__main__":
    print(bench())
"""

    if name == "evenodd":
        return f"""import sys
sys.setrecursionlimit({limit})

def is_even(n):
    if n == 0:
        return 1
    return is_odd(n - 1)

def is_odd(n):
    if n == 0:
        return 0
    return is_even(n - 1)

def bench():
    return is_even({n})

if __name__ == "__main__":
    print(bench())
"""

    raise KeyError(name)


def lua_source(name: str, params: dict[str, int]) -> str:
    """Той самий алгоритм для Lua 5.4; chunk повертає {bench = function}."""
    n = params["N"]

    if name == "fib":
        return f"""local function fib(n)
  if n == 0 then return 0 end
  if n == 1 then return 1 end
  return fib(n - 1) + fib(n - 2)
end

local function bench()
  return fib({n})
end

return {{ bench = bench }}
"""

    if name == "loop":
        return f"""local function loop(n, acc)
  if n == 0 then return acc end
  return loop(n - 1, acc + 2)
end

local function bench()
  return loop({n}, 0)
end

return {{ bench = bench }}
"""

    if name == "ackermann":
        return f"""local function ack(m, n)
  if m == 0 then return n + 1 end
  if n == 0 then return ack(m - 1, 1) end
  return ack(m - 1, ack(m, n - 1))
end

local function bench()
  return ack(3, {n})
end

return {{ bench = bench }}
"""

    if name == "closures":
        return f"""local function make_adder(k)
  return function(x)
    return x + k
  end
end

local add3 = make_adder(3)

local function loop(n, acc)
  if n == 0 then return acc end
  return loop(n - 1, add3(acc))
end

local function bench()
  return loop({n}, 0)
end

return {{ bench = bench }}
"""

    if name == "evenodd":
        return f"""local is_even
local is_odd

is_even = function(n)
  if n == 0 then return 1 end
  return is_odd(n - 1)
end

is_odd = function(n)
  if n == 0 then return 0 end
  return is_even(n - 1)
end

local function bench()
  return is_even({n})
end

return {{ bench = bench }}
"""

    raise KeyError(name)


def run_checked(
    cmd: list[str],
    *,
    expected: str | None = None,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"команда впала ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    if expected is not None:
        got_lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        got = got_lines[-1] if got_lines else ""
        if got != expected:
            raise RuntimeError(
                f"неправильна відповідь: {' '.join(cmd)}: "
                f"expected={expected!r}, got={got!r}"
            )
    return proc


def instruction_count(cmd: list[str]) -> int:
    proc = subprocess.run(
        [
            "valgrind",
            "--tool=cachegrind",
            "--cache-sim=no",
            "--cachegrind-out-file=/dev/null",
            *cmd,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"valgrind-команда впала ({proc.returncode}): {' '.join(cmd)}\n"
            f"{proc.stderr}"
        )
    match = re.search(r"I\s+refs:\s*([\d,]+)", proc.stderr)
    if match is None:
        raise RuntimeError(f"Cachegrind не повернув I refs:\n{proc.stderr}")
    return int(match.group(1).replace(",", ""))


def runtime_metrics(cmd: list[str]) -> dict[str, float | int]:
    started = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    _pid, status, usage = os.wait4(proc.pid, 0)
    wall = time.perf_counter() - started
    stdout = proc.stdout.read() if proc.stdout is not None else ""
    stderr = proc.stderr.read() if proc.stderr is not None else ""
    if proc.stdout is not None:
        proc.stdout.close()
    if proc.stderr is not None:
        proc.stderr.close()
    exit_code = os.waitstatus_to_exitcode(status)
    if exit_code != 0:
        raise RuntimeError(
            f"native-команда впала ({exit_code}): {' '.join(cmd)}\n"
            f"stdout:\n{stdout}\nstderr:\n{stderr}"
        )
    return {
        "wall_s": wall,
        "user_s": usage.ru_utime,
        "sys_s": usage.ru_stime,
        "maxrss_kb": usage.ru_maxrss,
    }


def git_fact(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception as exc:  # noqa: BLE001 — це лише факт середовища.
        return f"unknown ({exc})"


def command_set(
    sens_bench: Path,
    python: str,
    lua: str,
    racket: str,
    workdir: Path,
    name: str,
    inner_reps: int,
) -> dict[str, dict[str, list[str]]]:
    py_file = workdir / f"{name}.py"
    lua_file = workdir / f"{name}.lua"
    racket_file = workdir / f"{name}.rkt"
    return {
        "sens": {
            "load": [str(sens_bench), str(workdir), name, "sens", "load"],
            "ready": [str(sens_bench), str(workdir), name, "sens", "ready"],
            "repeat": [
                str(sens_bench), str(workdir), name, "sens", "repeat", str(inner_reps)
            ],
            "full": [str(sens_bench), str(workdir), name, "sens", "full"],
        },
        "cpython": {
            "load": [python, str(CPYTHON_DRIVER), str(py_file), "load"],
            "ready": [python, str(CPYTHON_DRIVER), str(py_file), "ready"],
            "repeat": [
                python,
                str(CPYTHON_DRIVER),
                str(py_file),
                "repeat",
                str(inner_reps),
            ],
            "full": [python, str(py_file)],
        },
        "lua": {
            "load": [lua, str(LUA_DRIVER), str(lua_file), "load"],
            "ready": [lua, str(LUA_DRIVER), str(lua_file), "ready"],
            "repeat": [
                lua,
                str(LUA_DRIVER),
                str(lua_file),
                "repeat",
                str(inner_reps),
            ],
            "full": [lua, str(LUA_DRIVER), str(lua_file), "full"],
        },
        "racket": {
            "load": [racket, str(RACKET_DRIVER), str(racket_file), "load"],
            "ready": [racket, str(RACKET_DRIVER), str(racket_file), "ready"],
            "repeat": [
                racket,
                str(RACKET_DRIVER),
                str(racket_file),
                "repeat",
                str(inner_reps),
            ],
            "full": [racket, str(RACKET_DRIVER), str(racket_file), "full"],
        },
    }


def median(rows, key):
    return statistics.median(rows[key])


def geomean(values):
    return math.exp(sum(math.log(value) for value in values) / len(values))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sens-bench", required=True, type=Path)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--lua", default="lua", help="Lua 5.4 executable")
    parser.add_argument("--racket", default="racket", help="Racket CS executable")
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument(
        "--inner-reps",
        type=int,
        default=3,
        help="скільки call-ів ампліфікувати під Cachegrind",
    )
    parser.add_argument(
        "--native-inner-reps",
        type=int,
        default=100,
        help="скільки call-ів ампліфікувати для native wall/CPU виміру",
    )
    parser.add_argument("--only", default=",".join(CASES))
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()

    selected = tuple(name for name in args.only.split(",") if name)
    unknown = sorted(set(selected) - set(CASES))
    if unknown:
        parser.error(f"невідомі workload: {', '.join(unknown)}")
    if args.reps < 1:
        parser.error("--reps має бути >= 1")
    if args.inner_reps < 1:
        parser.error("--inner-reps має бути >= 1")
    if args.native_inner_reps < 1:
        parser.error("--native-inner-reps має бути >= 1")

    lua_version_proc = run_checked([args.lua, "-v"])
    lua_version = (lua_version_proc.stdout or lua_version_proc.stderr).strip()
    if not lua_version.startswith("Lua 5.4"):
        raise RuntimeError(
            f"#1547 requires Lua 5.4, got {lua_version!r} from {args.lua!r}"
        )

    racket_version_proc = run_checked([args.racket, "--version"])
    racket_version = (racket_version_proc.stdout or racket_version_proc.stderr).strip()
    if "[cs]" not in racket_version.lower():
        raise RuntimeError(
            f"#1548 requires Racket CS, got {racket_version!r} from {args.racket!r}"
        )

    sens_surface = load_sens_surface_module()
    workdir = Path(tempfile.mkdtemp(prefix="sens-cross-bench-"))

    expected_by_name: dict[str, str] = {}
    for name in selected:
        workload = sens_surface.WORKLOADS[name]
        params = PARAMS[name]
        expected = workload["expected"](params)
        expected_by_name[name] = expected

        (workdir / f"{name}-sens.setup.lisp").write_text(
            sens_surface.render(workload["setup"], "sens", params),
            encoding="utf-8",
        )
        (workdir / f"{name}-sens.call.lisp").write_text(
            sens_surface.render(workload["call"], "sens", params) + "\n",
            encoding="utf-8",
        )
        (workdir / f"{name}.expected").write_text(expected + "\n", encoding="utf-8")
        (workdir / f"{name}.py").write_text(
            python_source(name, params),
            encoding="utf-8",
        )
        (workdir / f"{name}.lua").write_text(
            lua_source(name, params),
            encoding="utf-8",
        )
        (workdir / f"{name}.rkt").write_text(
            racket_adapter.source(name, params),
            encoding="utf-8",
        )

        # SENS FASL створюється до заміру; encode ніколи не входить у число.
        run_checked(
            [str(args.sens_bench), str(workdir), name, "sens", "encode"]
        )

    # Правильність — до будь-якого виміру.
    for name in selected:
        commands = command_set(
            args.sens_bench,
            args.python,
            args.lua,
            args.racket,
            workdir,
            name,
            args.inner_reps,
        )
        run_checked(commands["sens"]["full"])
        run_checked(commands["cpython"]["full"], expected=expected_by_name[name])
        run_checked(commands["lua"]["full"], expected=expected_by_name[name])
        run_checked(commands["racket"]["full"], expected=expected_by_name[name])
        print(
            f"[check] {name}: SENS=OK CPython=OK Lua=OK RacketCS=OK "
            f"expected={expected_by_name[name]}"
        )

    if args.check_only:
        return 0

    startup_commands = {
        "sens": [str(args.sens_bench), str(workdir), "empty", "-"],
        "cpython": [args.python, "-c", "pass"],
        "lua": [args.lua, "-e", ""],
        "racket": [args.racket, "-e", "(void)"],
    }

    rows: list[tuple[str, str, str, int, int]] = []
    runtime_rows: list[tuple[str, str, str, int, float, float, float, int]] = []
    for rep in range(1, args.reps + 1):
        for implementation, cmd in startup_commands.items():
            rows.append(
                (implementation, "empty", "startup", rep, instruction_count(cmd))
            )
            metrics = runtime_metrics(cmd)
            runtime_rows.append(
                (
                    implementation,
                    "empty",
                    "startup",
                    rep,
                    float(metrics["wall_s"]),
                    float(metrics["user_s"]),
                    float(metrics["sys_s"]),
                    int(metrics["maxrss_kb"]),
                )
            )
        for name in selected:
            instruction_commands = command_set(
                args.sens_bench,
                args.python,
                args.lua,
                args.racket,
                workdir,
                name,
                args.inner_reps,
            )
            native_commands = command_set(
                args.sens_bench,
                args.python,
                args.lua,
                args.racket,
                workdir,
                name,
                args.native_inner_reps,
            )
            for implementation in ("sens", "cpython", "lua", "racket"):
                for mode in ("load", "ready", "repeat", "full"):
                    count = instruction_count(instruction_commands[implementation][mode])
                    rows.append((implementation, name, mode, rep, count))
                    native_cmd = native_commands[implementation][mode]
                    metrics = runtime_metrics(native_cmd)
                    runtime_rows.append(
                        (
                            implementation,
                            name,
                            mode,
                            rep,
                            float(metrics["wall_s"]),
                            float(metrics["user_s"]),
                            float(metrics["sys_s"]),
                            int(metrics["maxrss_kb"]),
                        )
                    )
        print(f"[measure] repetition {rep}/{args.reps}")

    grouped = defaultdict(list)
    for implementation, name, mode, _rep, count in rows:
        grouped[(implementation, name, mode)].append(count)

    runtime_grouped = defaultdict(list)
    for implementation, name, mode, _rep, wall, user, sys_time, rss in runtime_rows:
        runtime_grouped[(implementation, name, mode, "wall_s")].append(wall)
        runtime_grouped[(implementation, name, mode, "user_s")].append(user)
        runtime_grouped[(implementation, name, mode, "sys_s")].append(sys_time)
        runtime_grouped[(implementation, name, mode, "maxrss_kb")].append(rss)

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    out = Path(args.out) if args.out else (
        ROOT / "benchmarks" / "cross-language" / "results"
        / f"{stamp}-{git_fact('rev-parse', '--short=8', 'HEAD')}"
    )
    out.mkdir(parents=True, exist_ok=True)

    with (out / "instructions.tsv").open("w", encoding="utf-8") as handle:
        handle.write("implementation\tworkload\tmode\trep\tinstructions\n")
        for row in rows:
            handle.write("\t".join(map(str, row)) + "\n")

    with (out / "runtime.tsv").open("w", encoding="utf-8") as handle:
        handle.write(
            "implementation\tworkload\tmode\trep\twall_s\tuser_s\tsys_s\tmaxrss_kb\n"
        )
        for row in runtime_rows:
            handle.write("\t".join(map(str, row)) + "\n")

    version_proc = run_checked([args.python, "--version"])
    python_version = (version_proc.stdout or version_proc.stderr).strip()
    environment = {
        "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "git_sha": git_fact("rev-parse", "HEAD"),
        "python": python_version,
        "lua": lua_version,
        "racket": racket_version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "sens_bench": str(args.sens_bench.resolve()),
        "reps": args.reps,
        "inner_reps": args.inner_reps,
        "native_inner_reps": args.native_inner_reps,
        "cases": list(selected),
        "params": {name: PARAMS[name] for name in selected},
        "metrics": [
            "valgrind cachegrind I refs",
            "native wall/user/sys time",
            "native maxrss_kb",
        ],
    }
    (out / "environment.json").write_text(
        json.dumps(environment, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    def startup(implementation: str) -> float:
        return median(grouped, (implementation, "empty", "startup"))

    def load_net(implementation: str, name: str) -> float:
        return median(grouped, (implementation, name, "load")) - startup(implementation)

    def setup_net(implementation: str, name: str) -> float:
        return (
            median(grouped, (implementation, name, "ready"))
            - median(grouped, (implementation, name, "load"))
        )

    def execution_net(implementation: str, name: str) -> float:
        delta = (
            median(grouped, (implementation, name, "repeat"))
            - median(grouped, (implementation, name, "ready"))
        )
        if delta <= 0:
            raise RuntimeError(
                f"{implementation}/{name}: repeat-ready={delta} <= 0; "
                "збільш --inner-reps, не маскуй шум"
            )
        return delta / args.inner_reps

    implementations = ("sens", "cpython", "lua", "racket")
    labels = {
        "sens": "SENS",
        "cpython": "CPython",
        "lua": "Lua 5.4",
        "racket": "Racket CS",
    }

    lines = [
        "# SENS ↔ CPython ↔ Lua 5.4 ↔ Racket CS: benchmark реалізацій",
        "",
        "Мірило: Valgrind Cachegrind I refs, медіана повторів. "
        "Це не рейтинг абстрактних мов.",
        "",
        "## Startup",
        "",
        "| реалізація | інструкції | відносно SENS |",
        "|---|---:|---:|",
    ]
    sens_startup = startup("sens")
    for implementation in implementations:
        value = startup(implementation)
        lines.append(
            f"| {labels[implementation]} | {value:,.0f} | ×{value / sens_startup:.3f} |"
        )

    lines += [
        "",
        "## Cold one-shot = process + load/setup + one call",
        "",
        "| workload | SENS full | CPython full | Lua 5.4 full | Racket CS full | CPython/SENS | Lua/SENS | Racket/SENS |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in selected:
        sens_full = median(grouped, ("sens", name, "full"))
        cpython_full = median(grouped, ("cpython", name, "full"))
        lua_full = median(grouped, ("lua", name, "full"))
        racket_full = median(grouped, ("racket", name, "full"))
        lines.append(
            f"| {name} | {sens_full:,.0f} | {cpython_full:,.0f} | {lua_full:,.0f} | "
            f"{racket_full:,.0f} | ×{cpython_full / sens_full:.3f} | "
            f"×{lua_full / sens_full:.3f} | ×{racket_full / sens_full:.3f} |"
        )

    lines += [
        "",
        f"## Steady execution = (repeat({args.inner_reps}) - ready) / {args.inner_reps}",
        "",
        "| workload | SENS | CPython | Lua 5.4 | Racket CS | CPython/SENS | Lua/SENS | Racket/SENS |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    cpython_ratios = []
    lua_ratios = []
    racket_ratios = []
    for name in selected:
        sens = execution_net("sens", name)
        cpython = execution_net("cpython", name)
        lua = execution_net("lua", name)
        racket = execution_net("racket", name)
        cpython_ratio = cpython / sens
        lua_ratio = lua / sens
        racket_ratio = racket / sens
        cpython_ratios.append(cpython_ratio)
        lua_ratios.append(lua_ratio)
        racket_ratios.append(racket_ratio)
        lines.append(
            f"| {name} | {sens:,.0f} | {cpython:,.0f} | {lua:,.0f} | {racket:,.0f} | "
            f"×{cpython_ratio:.3f} | ×{lua_ratio:.3f} | ×{racket_ratio:.3f} |"
        )

    lines += [
        "",
        "Геометричні середні нижче — лише компактний опис цього конкретного "
        "корпусу, не рейтинг мов.",
        f"Корпусне CPython/SENS: **×{geomean(cpython_ratios):.3f}**.",
        f"Корпусне Lua/SENS: **×{geomean(lua_ratios):.3f}**.",
        f"Корпусне Racket/SENS: **×{geomean(racket_ratios):.3f}**.",
        "",
        "## Load - startup",
        "",
        "| workload | SENS FASL decode | CPython source compile | Lua source compile | Racket source compile | CPython/SENS | Lua/SENS | Racket/SENS |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in selected:
        sens = load_net("sens", name)
        cpython = load_net("cpython", name)
        lua = load_net("lua", name)
        racket = load_net("racket", name)
        lines.append(
            f"| {name} | {sens:,.0f} | {cpython:,.0f} | {lua:,.0f} | {racket:,.0f} | "
            f"×{cpython / sens:.3f} | ×{lua / sens:.3f} | ×{racket / sens:.3f} |"
        )

    lines += [
        "",
        "## Setup = ready - load",
        "",
        "| workload | SENS setup | CPython module setup | Lua chunk setup | Racket module setup | CPython/SENS | Lua/SENS | Racket/SENS |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in selected:
        sens = setup_net("sens", name)
        cpython = setup_net("cpython", name)
        lua = setup_net("lua", name)
        racket = setup_net("racket", name)
        cpython_ratio = cpython / sens if sens > 0 else float("nan")
        lua_ratio = lua / sens if sens > 0 else float("nan")
        racket_ratio = racket / sens if sens > 0 else float("nan")
        lines.append(
            f"| {name} | {sens:,.0f} | {cpython:,.0f} | {lua:,.0f} | {racket:,.0f} | "
            f"×{cpython_ratio:.3f} | ×{lua_ratio:.3f} | ×{racket_ratio:.3f} |"
        )

    lines += [
        "",
        "## Operational wall time і RSS (спостереження, не CI-контракт)",
        "",
        "| workload | SENS wall/call | CPython wall/call | Lua wall/call | Racket wall/call | CPython/SENS | Lua/SENS | Racket/SENS | SENS RSS | CPython RSS | Lua RSS | Racket RSS |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in selected:
        wall = {}
        rss = {}
        for implementation in implementations:
            wall[implementation] = (
                median(runtime_grouped, (implementation, name, "repeat", "wall_s"))
                - median(runtime_grouped, (implementation, name, "ready", "wall_s"))
            ) / args.native_inner_reps
            rss[implementation] = median(
                runtime_grouped, (implementation, name, "repeat", "maxrss_kb")
            )
        lines.append(
            f"| {name} | {wall['sens']:.6f} | {wall['cpython']:.6f} | {wall['lua']:.6f} | "
            f"{wall['racket']:.6f} | ×{wall['cpython'] / wall['sens']:.3f} | "
            f"×{wall['lua'] / wall['sens']:.3f} | ×{wall['racket'] / wall['sens']:.3f} | "
            f"{rss['sens']:,.0f} | {rss['cpython']:,.0f} | {rss['lua']:,.0f} | {rss['racket']:,.0f} |"
        )

    lines += [
        "",
        f"Wall/RSS міряються окремим нативним repeat({args.native_inner_reps}) "
        "без Valgrind; тому вони не містять overhead Cachegrind.",
        "",
        "## Межі інтерпретації",
        "",
        "- SENS load — декодування заздалегідь створеного FASL; encode не міряється.",
        "- CPython load — matched driver: читання source + compile(...), без виконання модулю.",
        "- Lua load — matched Lua 5.4 driver: loadfile(source), без виконання chunk.",
        "- Racket load — matched Racket CS driver: read-syntax + compile(module), без instantiation.",
        f"- Steady execution — (repeat({args.inner_reps}) - ready) / {args.inner_reps}; "
        "ready і repeat проходять matched load/setup path у кожній реалізації.",
        "- CPython, Lua і Racket repeat мають мінімальний loop у своїх driver; SENS repeat має "
        "мінімальний Rust loop. Це явно лишається частиною measurement harness.",
        f"- Cachegrind використовує repeat({args.inner_reps}); native wall/CPU — "
        f"repeat({args.native_inner_reps}), щоб process noise не домінував короткі workload.",
        "- Усі відповіді чотирьох реалізацій перевірені до вимірювання.",
        "",
    ]

    report = "\n".join(lines)
    (out / "report.md").write_text(report, encoding="utf-8")
    print()
    print(report)
    print(f"\nРезультати: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
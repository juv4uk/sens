#!/usr/bin/env python3
"""Current Contract 11.5 load comparison: exact-domain SENS vs Lua 5.4.

Lua lanes:
- source load: loadfile(source), no chunk execution;
- source ready: loadfile + execute definitions, no bench() call;
- bytecode load: loadfile(precompiled luac5.4 chunk), no execution;
- bytecode ready: load bytecode + execute definitions, no bench() call.

SENS lanes match #3562:
- startup;
- exact program load = read + parse + lower, no execution;
- cold-ready = Core bootstrap + parse/lower whole program + install definitions,
  no benchmark call.

Cachegrind I refs are primary. Wall time is auxiliary.
"""

from __future__ import annotations

import argparse
import math
import re
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

import current_sens as sens
import current_sens_phases as sens_phases

ROOT = Path(__file__).resolve().parents[2]
LUA_DRIVER = ROOT / "benchmarks" / "cross-language" / "lua_phase_driver.lua"


def lua_source(name: str) -> str:
    n = sens.PARAMS[name]
    if name == "fib":
        return f"""local function fib(n)
  if n == 0 then return 0 end
  if n == 1 then return 1 end
  return fib(n - 1) + fib(n - 2)
end

function bench()
  return fib({n})
end
"""
    if name == "loop":
        return f"""local function loop(n, acc)
  if n == 0 then return acc end
  return loop(n - 1, acc + 2)
end

function bench()
  return loop({n}, 0)
end
"""
    if name == "ackermann":
        return f"""local ack
ack = function(m, n)
  if m == 0 then return n + 1 end
  if n == 0 then return ack(m - 1, 1) end
  return ack(m - 1, ack(m, n - 1))
end

function bench()
  return ack(3, {n})
end
"""
    if name == "closures":
        return f"""local function make_adder(k)
  return function(x) return x + k end
end

local add3 = make_adder(3)

local function loop(n, acc)
  if n == 0 then return acc end
  return loop(n - 1, add3(acc))
end

function bench()
  return loop({n}, 0)
end
"""
    if name == "evenodd":
        return f"""local is_even, is_odd

is_even = function(n)
  if n == 0 then return true end
  return is_odd(n - 1)
end

is_odd = function(n)
  if n == 0 then return false end
  return is_even(n - 1)
end

function bench()
  return is_even({n}) and 1 or 0
end
"""
    raise KeyError(name)


def checked(cmd: list[str], expected: str | None = None) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    if expected is not None:
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        got = lines[-1] if lines else ""
        if got != expected:
            raise RuntimeError(
                f"wrong answer: {' '.join(cmd)} expected={expected!r} got={got!r}"
            )


def irefs(cmd: list[str]) -> int:
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
            f"cachegrind failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}"
        )
    match = re.search(r"I\s+refs:\s*([\d,]+)", proc.stderr)
    if match is None:
        raise RuntimeError(f"missing Cachegrind I refs:\n{proc.stderr}")
    return int(match.group(1).replace(",", ""))


def wall(cmd: list[str]) -> float:
    started = time.perf_counter()
    proc = subprocess.run(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=False
    )
    elapsed = time.perf_counter() - started
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}")
    return elapsed


def geomean(values: list[float]) -> float:
    return math.exp(sum(math.log(v) for v in values) / len(values))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sens-runner", required=True)
    ap.add_argument("--lua", default="lua5.4")
    ap.add_argument("--luac", default="luac5.4")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    if args.reps < 1:
        ap.error("--reps must be >= 1")

    version = subprocess.run(
        [args.lua, "-v"], capture_output=True, text=True, check=True
    )
    version_text = (version.stdout or version.stderr).strip()
    if "Lua 5.4" not in version_text:
        raise RuntimeError(f"Lua 5.4 required, got {version_text}")

    runner = str(Path(args.sens_runner).resolve())
    workdir = Path(tempfile.mkdtemp(prefix="sens-lua-load-"))
    files: dict[str, dict[str, Path]] = {}

    for name in sens.CASES:
        setup, call = sens_phases.setup_call(name)
        s_setup = workdir / f"{name}.setup.lisp"
        s_call = workdir / f"{name}.call.lisp"
        lua_src = workdir / f"{name}.lua"
        lua_bc = workdir / f"{name}.luac"

        s_setup.write_text(setup, encoding="utf-8")
        s_call.write_text(call, encoding="utf-8")
        lua_src.write_text(lua_source(name), encoding="utf-8")

        compile_proc = subprocess.run(
            [args.luac, "-o", str(lua_bc), str(lua_src)],
            capture_output=True,
            text=True,
            check=False,
        )
        if compile_proc.returncode != 0:
            raise RuntimeError(
                f"luac failed for {name}:\n{compile_proc.stdout}\n{compile_proc.stderr}"
            )

        files[name] = {
            "setup": s_setup,
            "call": s_call,
            "lua": lua_src,
            "luac": lua_bc,
        }

        expected = sens.EXPECTED[name]
        checked([runner, "steady", str(s_setup), str(s_call), "1"], expected)
        checked([args.lua, str(LUA_DRIVER), str(lua_src), "full"], expected)
        checked([args.lua, str(LUA_DRIVER), str(lua_bc), "full"], expected)
        print(f"[check] {name}: SENS/Lua source/Lua bytecode OK expected={expected}")

    rows: list[dict[str, object]] = []

    def measure(runtime: str, workload: str, phase: str, cmd: list[str]) -> None:
        for rep in range(1, args.reps + 1):
            rows.append(
                {
                    "runtime": runtime,
                    "workload": workload,
                    "phase": phase,
                    "rep": rep,
                    "i_refs": irefs(cmd),
                    "wall_s": wall(cmd),
                }
            )

    measure("sens-exact", "__global__", "startup", [runner, "startup"])
    measure("lua54-source", "__global__", "startup", [args.lua, "-e", "return"])

    for name in sens.CASES:
        f = files[name]
        measure(
            "sens-exact",
            name,
            "load",
            [runner, "lower", str(f["setup"]), str(f["call"])],
        )
        measure(
            "sens-exact",
            name,
            "cold-ready",
            [runner, "ready", str(f["setup"]), str(f["call"])],
        )
        for runtime, path in (
            ("lua54-source", f["lua"]),
            ("lua54-bytecode", f["luac"]),
        ):
            measure(
                runtime,
                name,
                "load",
                [args.lua, str(LUA_DRIVER), str(path), "load"],
            )
            measure(
                runtime,
                name,
                "cold-ready",
                [args.lua, str(LUA_DRIVER), str(path), "ready"],
            )

    args.out.mkdir(parents=True, exist_ok=True)
    fields = ("runtime", "workload", "phase", "rep", "i_refs", "wall_s")
    with (args.out / "lua-load-raw.tsv").open("w", encoding="utf-8") as fh:
        fh.write("\t".join(fields) + "\n")
        for row in rows:
            fh.write("\t".join(str(row[f]) for f in fields) + "\n")

    def med(runtime: str, workload: str, phase: str, field: str) -> float:
        vals = [
            float(r[field])
            for r in rows
            if r["runtime"] == runtime
            and r["workload"] == workload
            and r["phase"] == phase
        ]
        return statistics.median(vals)

    sens_start_i = med("sens-exact", "__global__", "startup", "i_refs")
    lua_start_i = med("lua54-source", "__global__", "startup", "i_refs")
    sens_start_w = med("sens-exact", "__global__", "startup", "wall_s")
    lua_start_w = med("lua54-source", "__global__", "startup", "wall_s")

    def net(runtime: str, name: str, phase: str, field: str) -> float:
        raw = med(runtime, name, phase, field)
        if runtime == "sens-exact":
            start = sens_start_i if field == "i_refs" else sens_start_w
        else:
            start = lua_start_i if field == "i_refs" else lua_start_w
        return raw - start

    lines = [
        "# Current exact-domain load: SENS vs Lua 5.4 source/bytecode",
        "",
        "Primary metric: Cachegrind I refs. Wall time is auxiliary.",
        "",
        f"SENS startup: {sens_start_i:,.0f} I refs / {sens_start_w * 1000:.3f} ms.",
        f"Lua 5.4 startup: {lua_start_i:,.0f} I refs / {lua_start_w * 1000:.3f} ms.",
        "",
        "## Load — no definitions executed",
        "",
        "| workload | SENS parse+lower | Lua source loadfile | Lua bytecode loadfile | source/SENS | bytecode/SENS |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    src_ratios: list[float] = []
    bc_ratios: list[float] = []
    for name in sens.CASES:
        s = net("sens-exact", name, "load", "i_refs")
        ls = net("lua54-source", name, "load", "i_refs")
        lb = net("lua54-bytecode", name, "load", "i_refs")
        src_ratios.append(ls / s)
        bc_ratios.append(lb / s)
        lines.append(
            f"| {name} | {s:,.0f} | {ls:,.0f} | {lb:,.0f} | {ls / s:.3f}x | {lb / s:.3f}x |"
        )

    lines += [
        "",
        f"Geomean Lua source / SENS load: **{geomean(src_ratios):.3f}x**.",
        f"Geomean Lua bytecode / SENS load: **{geomean(bc_ratios):.3f}x**.",
        "",
        "## Cold ready — definitions installed, bench() not called",
        "",
        "| workload | SENS Core+ready | Lua source ready | Lua bytecode ready | source/SENS | bytecode/SENS |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    src_ready: list[float] = []
    bc_ready: list[float] = []
    for name in sens.CASES:
        s = net("sens-exact", name, "cold-ready", "i_refs")
        ls = net("lua54-source", name, "cold-ready", "i_refs")
        lb = net("lua54-bytecode", name, "cold-ready", "i_refs")
        src_ready.append(ls / s)
        bc_ready.append(lb / s)
        lines.append(
            f"| {name} | {s:,.0f} | {ls:,.0f} | {lb:,.0f} | {ls / s:.3f}x | {lb / s:.3f}x |"
        )

    lines += [
        "",
        f"Geomean Lua source / SENS cold-ready: **{geomean(src_ready):.3f}x**.",
        f"Geomean Lua bytecode / SENS cold-ready: **{geomean(bc_ready):.3f}x**.",
        "",
        "Interpretation boundary:",
        "- Lua bytecode is produced with the same pinned Lua 5.4 toolchain before timing.",
        "- Lua load uses loadfile() only; returned chunks are not executed.",
        "- Lua ready executes the definitions chunk but does not call bench().",
        "- SENS load is exact-domain read + parse + lower for setup+call, no execution.",
        "- SENS cold-ready includes Core bootstrap and definition installation; benchmark call is prepared but not executed.",
        "- Warm resident-Core SENS is a separate slope experiment and must not be inferred from cold-ready.",
        "- No historical Sens8/Sid8/Function8 path participates.",
        "",
    ]

    report = "\n".join(lines)
    (args.out / "lua-load-report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

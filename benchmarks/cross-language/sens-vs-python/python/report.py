"""Statistics and report rendering from immutable raw benchmark JSON."""

import json
import math
import statistics
from pathlib import Path


def nearest_rank(values: list[int], percentile: int) -> int:
    if not values or not 1 <= percentile <= 100:
        raise ValueError("percentile requires nonempty values and a rank in 1..100")
    ordered = sorted(values)
    return ordered[math.ceil(percentile * len(ordered) / 100) - 1]


def summarize(run: dict) -> dict:
    values = [sample["elapsed_ns"] for sample in run["samples"]]
    if len(values) != run["n"]:
        raise ValueError("sample count does not match raw sample array")
    return {
        "implementation": run["implementation"], "n": len(values),
        "min_ns": min(values), "median_ns": int(round(statistics.median(values))),
        "p95_ns": nearest_rank(values, 95), "p99_ns": nearest_rank(values, 99), "max_ns": max(values),
        "rss_kib": run["rss_kib"],
    }


def render(run_dir: Path, manifest: dict, paired: dict, metadata: dict | None = None) -> str:
    metadata = metadata or {}
    host = metadata.get("host", {})
    git = metadata.get("git", {})
    lines = ["# Результати benchmark SENS vs CPython", "", f"Run: `{run_dir.name}`",
             f"SENS HEAD: `{git.get('commit', 'unknown')}` · CPython `{metadata.get('python', 'unknown').split()[0]}` · `{metadata.get('rustc', 'unknown')}`",
             f"Host: {host.get('hostname', 'unknown')} · {host.get('cpu_model', 'unknown')} · {host.get('os', 'unknown')}",
             f"SENS binary SHA-256: `{metadata.get('sens_runner_sha256', 'unknown')}` · manifest SHA-256: `{metadata.get('workloads_manifest_sha256', 'unknown')}`", "",
             f"Порядок пар workload-ів: `{json.dumps(metadata.get('execution_order', 'не записано'), ensure_ascii=False)}`.", "",
             "Таймінг включає лише виклик уже завантаженої реалізації. Запуск процесу, підготовка й перевірка parity виключені.", "",
             "Ratio `CPython/SENS` — медіана CPython, поділена на медіану SENS; значення нижче 1 означає менший час CPython.", "",
             "| Workload (параметри) | Статус | Реалізація | Parity | n | median (µs) | p95 (µs) | p99 (µs) | RSS baseline/peak/Δ (KiB) | CPython/SENS median |",
             "|---|---:|---|---|---:|---:|---:|---:|---:|---:|"]
    for item in manifest["workloads"]:
        workload_id = item["id"]
        parameters = ", ".join(f"{key}={value}" for key, value in item.get("parameters", {}).items()) or "—"
        result = paired.get(workload_id)
        if result is None:
            lines.append(f"| {workload_id} ({parameters}) | {item.get('status', 'BLOCKED').upper()} | — | — | — | — | — | — | — | — |")
            lines.append("")
            continue
        for implementation in ("SENS", "CPython source"):
            run = result.get(implementation)
            if run is None:
                lines.append(f"| {workload_id} ({parameters}) | BLOCKED | {implementation} | — | — | — | — | — | — | — |")
                continue
            stats = summarize(run)
            rss = stats["rss_kib"]
            ratio = "—"
            if implementation == "SENS":
                sens_median = stats["median_ns"]
                python_median = summarize(result["CPython source"])["median_ns"]
                ratio = f"{python_median / sens_median:.3f}×" if sens_median else "undefined"
            lines.append(f"| {workload_id} ({parameters}) | PASS | {implementation} | PASS | {stats['n']} | {stats['median_ns']/1000:.3f} | {stats['p95_ns']/1000:.3f} | {stats['p99_ns']/1000:.3f} | {rss['baseline_after_warmup']}/{rss['peak_vmhwm']}/{rss['delta_peak_from_baseline']} | {ratio} |")
        lines.append("")
    blocked = [row for row in manifest["workloads"] if row.get("status") == "blocked"]
    lines += ["## Обмеження", "", "p99 за 100 спостережень фактично є другим найбільшим значенням і не характеризує далекий хвіст. RSS — процесний VmRSS після warmup та VmHWM після вимірів; він включає середовище виконання й алокатор.", "", "Зіставляються однакові алгоритми, визначені у SENS source та Python `.py`. SENS виконує вже розібране/понижене source-дерево через поточний exact evaluator; CPython під час імпорту `.py` компілює його у внутрішній bytecode, але готовий `.pyc` не використовується. Таймінг не вимірює парсер або startup: він порівнює конкретні runtime-шляхи evaluator проти CPython VM, а не фізичні представлення чи властивість мов загалом.", "", "Збалансований повтор показав міжзапусковий розкид медіан, тому одиничні коефіцієнти не є стабільними константами. Загальний переможець не оголошується; workload-и відрізняються за навантаженням.", "", "Невиконані workload-и:"]
    translations = {
        "json-parse-serialize": "У поточному exact reader приймається D9 JSON-parse identity, але немає викличного Core runtime mechanism; змішане source-ім’я не зв’язане. Не підміняти історичним W8 builtin або host-парсером поза SENS.",
        "n-body": "Немає підтвердженої зіставної поточної числової семантики/точності SENS і CPython для запропонованого workload.",
        "mandelbrot": "Немає підтвердженої зіставної поточної числової семантики/точності SENS і CPython для запропонованого workload.",
        "regex": "Не визначено спільний regex engine і контракт поведінки.",
    }
    lines.extend(f"- `{row['id']}`: {translations.get(row['id'], row.get('reason', 'недостатньо придатних зіставних даних'))}" for row in blocked)
    lines += ["", "Повні raw samples і метадані лежать у `raw/`; графіки побудовано без фільтрації samples.", ""]
    return "\n".join(lines)


def load(path: Path) -> dict:
    return json.loads(path.read_text())

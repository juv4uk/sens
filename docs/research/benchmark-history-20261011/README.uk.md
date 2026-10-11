# Історичні бенчмарки SENS: перша партія (11.10.2026)

Першоджерела з PR #5517, #5514, #5508, #5500, #3185, #3128, #5214, #5192 інтегровано до main в **невиконуваний доказовий архів**. Файли мають оригінальний Git blob SHA: жодної зміни сирцевих байтів. Повторні SHA між PR навмисні й свідчать про спільний донорський код.

Дослідні режими: sweep 41 зареєстрованого тесту, D6 parity, execution ladder, Rust serde_json/SENS wire, незалежні CPython/Lua/Racket контролі, фізичні T5 проєкції, packed vs visible. Архівування не свідчить про відтворене прискорення і не встановлює новий канонічний кодек. Запуск і перенесення в активний `benchmarks/` дозволяються лише після перевірки поточних входів, exact SHA, достовірності timing і механічних регресій.

- PR #5517: `benchmarks/d6-parity-duality/bench.json` Git blob `5c69fde142e7e4cbd8aaa0d52296d2569d1d506a`
- PR #5517: `benchmarks/execution-ladder-objective/bench.json` Git blob `a17c82e579a120df6c81e96f94d650fdee4166b2`
- PR #5517: `scripts/benchmark_sweep.py` Git blob `f344f999ba863c81f343c76858c592755d8756f7`
- PR #5517: `scripts/summarize_benchmark_sweep.py` Git blob `5d775b64c3786c67fa06e44e8b95bf806cd2ecfb`
- PR #5514: `scripts/benchmark_sweep.py` Git blob `f344f999ba863c81f343c76858c592755d8756f7`
- PR #5508: `benchmarks/d6-parity-duality/bench.json` Git blob `5c69fde142e7e4cbd8aaa0d52296d2569d1d506a`
- PR #5508: `benchmarks/execution-ladder-objective/bench.json` Git blob `a17c82e579a120df6c81e96f94d650fdee4166b2`
- PR #5500: `scripts/benchmark_sweep.py` Git blob `f344f999ba863c81f343c76858c592755d8756f7`
- PR #3185: `crates/sens/examples/transport_decode_bench.rs` Git blob `f76a33447b5f28cc4c15d9182d1cde9b8d1bef99`
- PR #3128: `benchmarks/cross-language/README.md` Git blob `fd56ca168e8680da9fa297d820981c40e0260aa7`
- PR #3128: `benchmarks/cross-language/external_controls.py` Git blob `780ff751b4afbacd39eaab23e3911c2ff510d6dc`
- PR #3128: `benchmarks/cross-language/manifest.scm` Git blob `c685a932967bfde74efb2b86045ead8164395a3b`
- PR #5214: `crates/sens/examples/t5_view_ab.rs` Git blob `26ee41c1a71530a269e3b8962e81873821bd8b5e`
- PR #5192: `benchmarks/packed-vs-visible/README.md` Git blob `6b4abbdc8ff58364f7b2f3c2eccfa762548241a6`
- PR #5192: `benchmarks/packed-vs-visible/bench.json` Git blob `351fc01674d1fdb208865c1bce652b7492b17664`
- PR #5192: `crates/sens/examples/packed_vs_visible_bench.rs` Git blob `e74b6dc8346294f260c10dba0b750dedecd00f78`

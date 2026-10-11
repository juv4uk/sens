# Історичні SENS бенчмарки, друга партія

Джерела із 12 незлитих PR, перевірені за оригінальним Git blob SHA й збережені **без редагування** в main як нормативно неактивні оракули вимірювання. Охоплено реальний T5 hot path, native machine, SBCL, Racket, Lua, CPython, парні A/B вимірювання, Criterion/I-ref verdict, STORE→AIR→LOAD, unbounded-width та фазовий профіль SENS.

Кожен файл у `prN/<оригінальний-шлях>`. Жодні старі часові цифри не є вимірюванням поточного main. До активного benchmark registry можна перенести лише після перевірки ревізії, fixtures, машинного обладнання, холодного/теплого режиму, незалежного оракула та відтворення.

- #5221 `benchmarks/physical-sens-runtime/hot.py` — `7ee22d1fc4f85df6b01cd3fa61c729d72a8629c8`
- #5221 `crates/sens/examples/physical_sens_hot_bench.rs` — `4790c2db8088b50fd821f0b7f29547cc80ae4878`
- #5280 `benchmarks/native-machine-1/README.md` — `a5e2794e0b4d4f7f4decdbabadf4ea2c4448a941`
- #5280 `benchmarks/native-machine-1/bench.json` — `db4b3d371956ac984cb57a930943797a1d7fb087`
- #5280 `benchmarks/native-machine-1/summarize.py` — `0b6f4ab4b96fe570f26722217388e7dec3018ddd`
- #5280 `crates/sens-host/examples/native_machine_bench.rs` — `1302209ea276334665069c990b404bc77f3ad2fe`
- #5278 `benchmarks/native-zero/README.md` — `ec41cfb1785e89f3b398c164fc4d22f9b19e2154`
- #5278 `benchmarks/native-zero/bench.json` — `6206122f74130d4f75e4f209acebd90f609368e0`
- #5278 `benchmarks/native-zero/verify_report.py` — `28ce1128df2781a99208d64f142cf2864ddfcf4b`
- #3574 `benchmarks/cross-language/current_sbcl_load.py` — `6833e7bcb94280ff82f57b27d3cabba9127fd8f9`
- #3573 `benchmarks/cross-language/current_racket_load.py` — `378e79006e5089c1985257c0e2cd7ab84b5707b7`
- #3573 `benchmarks/cross-language/racket_phase_driver.rkt` — `55d4919c71b1fcaf6c4bd027a7e2074f0c7f6680`
- #3570 `benchmarks/cross-language/current_lua_load.py` — `29c86a064b256f094555ab0f38d22802e51f1eff`
- #3570 `benchmarks/cross-language/lua_phase_driver.lua` — `d10c9a86a7a0a1ec14ad5114384734dffd60e0f6`
- #3562 `benchmarks/cross-language/current_load_formats.py` — `5371625dc88cb189e4959080e65477778ac58fcb`
- #5228 `benchmarks/methodology/README.md` — `77af2e6deac8c49fbdd12096e7636f9176ab5d7a`
- #5228 `benchmarks/methodology/paired_wall.py` — `93aa826080b7ba63cde3b488b6a95d41b871a1fe`
- #5228 `benchmarks/methodology/tests/test_paired_wall.py` — `2fc0b27024cfc3376e4f7111fddd0be7cc3d20c0`
- #5230 `benchmarks/measurement-triad/README.md` — `dc09508ae60eb5764fd0be0d66d68e08593c83c1`
- #5230 `benchmarks/measurement-triad/bench.json` — `7cf3d139988c83ba26a0cfe74fbaa045b29e09ac`
- #5230 `benchmarks/measurement-triad/verdict.py` — `434dda726ac85b312a8b6cbdba8f42223d9f4003`
- #5230 `benchmarks/measurement-triad/test_verdict.py` — `fb3df2df3a8cfe48a499dbe25b356029b88b70eb`
- #3605 `benchmarks/store-air-load/README.md` — `d2debdbe25626a3d4ce1b9d56f11ac1d13eca096`
- #3605 `benchmarks/store-air-load/fixtures.json` — `1843b22d5257330d9a0bc57e5e5ad1d65c60e6dd`
- #3605 `benchmarks/store-air-load/run.py` — `2e48267a8ef294653b4ae69cac0818ee5ead47f6`
- #3605 `benchmarks/store-air-load/schema.json` — `7981ea278e8e49a7e671f4ede351b0467017ab4b`
- #3605 `benchmarks/store-air-load/validate.py` — `d20a69431cce1acc707138115339b7b3c424247f`
- #2005 `benchmarks/unbounded-width/README.uk.md` — `b471008f1f4be7cc1d9caaa32bf51dcd5dadda29`
- #2005 `benchmarks/unbounded-width/run.py` — `422e33e6b93d2b1c0c356f9cf6df372937f74d0e`
- #2005 `benchmarks/unbounded-width/width_scale.c` — `72d8593012a5d79c231d5b8f03db929d3e66e07f`
- #3493 `benchmarks/cross-language/core_load_breakdown.py` — `01612a2088e8a8dca2a42dc39eabe05b2baaf15c`
- #3493 `benchmarks/cross-language/current_sens_phases.py` — `5340375e1827fc8706b7a7ea9518ad92e95d35b7`

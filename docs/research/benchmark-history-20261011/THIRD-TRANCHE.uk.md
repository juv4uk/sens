# Історичні бенчмарки — третя партія (11.10.2026)

Збережено 20 оригінальних Git blobs із 12 PR. Досліди: D4/D5 ширини, облік генерації, footprint/Pareto, економіка селекторів D6, фази виконання D1–D8, proof-check execution ladder, C dispatch D3/D4, внутрішній bootstrap і зовнішні контролі SBCL/Racket/Lua/CPython. Історичні значення не є доведеними вимірюваннями поточного main. Досліди виконувати лише після перенесення під чинні оракули та benchmark registry.

- PR #2217: `scripts/bench-2214-domain-width-pareto.py` SHA `2f8a231ef93dd4f82a71312ec90e6350bd2b4917`
- PR #2217: `docs/research/2214-domain-width-pareto.uk.md` SHA `4f6a941616d6e44f9fc9abd9155d3e5da9743220`
- PR #2412: `benchmarks/generation-accounting/run.py` SHA `cecf13f933ac95c57f0cb451afda8973ffd5367b`
- PR #3607: `benchmarks/cross-language/footprint_controls.py` SHA `b68b0ab5f99fccbbc1581a924156ce2ada622871`
- PR #3607: `benchmarks/cross-language/pareto_report.py` SHA `babdcf5808675e32cf437463d3ad48256fb6e24f`
- PR #3607: `benchmarks/cross-language/test_pareto_report.py` SHA `68ab8b30182329c65f17df97420728cab028c217`
- PR #3649: `benchmarks/generator-economy/README.md` SHA `dd6464fda83474b92f95e9e605af76e351a4f477`
- PR #3649: `benchmarks/generator-economy/current_closure.py` SHA `8ceeeeabaa310b54ba9e651bebadae16dbe95212`
- PR #4194: `benchmarks/current-en-vs-d1d8/phase_replay.py` SHA `2a8a4b15883937823becd3868d401787d558efc3`
- PR #4152: `benchmarks/execution-ladder-conformance/emit_oracle.py` SHA `524716cdaeb5dcb545b67d30c727280ea41b3593`
- PR #4152: `benchmarks/execution-ladder-conformance/generate_bounded.py` SHA `bc37b27030cbed8d66fbbf9eb085713fc14f916c`
- PR #4152: `benchmarks/execution-ladder-conformance/validate.py` SHA `32461f2df3e5c2ef7dfbf4459785f15dfbcad179`
- PR #3791: `benchmarks/domain1234-dispatch/README.md` SHA `37b9025aed665e2333908ef6754a3fd53564d118`
- PR #3791: `benchmarks/domain1234-dispatch/d34_dispatch.c` SHA `c52717f4fd948d517af2f9a7b9e8d07c80f69ec3`
- PR #3791: `benchmarks/domain1234-dispatch/run.py` SHA `d77217c33b3a414c5bc75ac1a49b76c6c1154cd8`
- PR #3654: `benchmarks/core-bootstrap-internal/run.py` SHA `89c2596c63de247c7370368b5e374af74799d47a`
- PR #3579: `benchmarks/cross-language/current_sbcl_load.py` SHA `6833e7bcb94280ff82f57b27d3cabba9127fd8f9`
- PR #3578: `benchmarks/cross-language/current_racket_load.py` SHA `378e79006e5089c1985257c0e2cd7ab84b5707b7`
- PR #3577: `benchmarks/cross-language/current_lua_load.py` SHA `29c86a064b256f094555ab0f38d22802e51f1eff`
- PR #3576: `benchmarks/cross-language/current_load_formats.py` SHA `5371625dc88cb189e4959080e65477778ac58fcb`

#!/usr/bin/env sh
# Відтворюваний диференційний доказ Rust<->Python для дослідного кодека.
# Позитивні вектори: Python-оракул (adaptive_encoder/research_codec/tb33)
# емітує байти, Rust-модуль мусить дати побайтовий збіг на кожному кроці.
# Негативні вектори: обидві реалізації мусять відмовити.
set -eu
cd "$(dirname "$0")"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

python3 gen_vectors.py > "$work/positive.tsv"
python3 gen_negatives.py > "$work/negative.tsv"
rustc --edition 2021 -O parity.rs -o "$work/parity"
cat "$work/positive.tsv" "$work/negative.tsv" | "$work/parity"

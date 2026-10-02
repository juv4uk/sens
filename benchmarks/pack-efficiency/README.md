# Packed payload efficiency benchmark (#2190)

This benchmark measures the production `Bits<N>` / `BitPacker` / `PackedBitstream`
mechanics. It does not assign language meaning and does not choose a wire framing.

Compared lanes:

1. one u8 payload byte per logical word;
2. dense sequential packed payload;
3. packed payload decoded once into a cached u8 view.

The exact width schedule is supplied out-of-band to every lane. That keeps
#2189 framing/boundary metadata outside this benchmark and makes the CPU
comparison like-for-like.

Primary metric: Cachegrind I refs. Branches are recorded too. Each result
separates logical preparation, packing, one-time decode, and repeated scans.

Cases include homogeneous widths W1 through W8 plus explicit synthetic mixed
width schedules. They are mechanical controls, not claims about a current
whole-program source corpus.

The key crossover is:

```text
decode packed once + scan cached N times
vs
scan packed directly N times
```

The report computes the N where caching becomes cheaper.

Run:

```bash
cargo build --release -p sens --example pack_efficiency_bench
python3 benchmarks/pack-efficiency/run.py \
  --binary target/release/examples/pack_efficiency_bench \
  --out /tmp/pack-efficiency
```

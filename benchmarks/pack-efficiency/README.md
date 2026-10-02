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


## Random access and size scaling

`random_scale.py` extends the same production benchmark with deterministic
indexed reads and explicit boundary-accounting.

Compared hot query lanes:

1. u8-per-word direct index;
2. packed `PackedBitstream::read` at a known offset;
3. decode-once u8 cache direct index.

For fixed-width W1..W8 controls, packed offsets are derived as `index * width`
and require no offset table. Mixed variable-width schedules use an explicit
host `usize` offset-index proxy; its bytes are reported separately rather
than hidden in the packed-payload number.

The runner records Cachegrind I refs plus D1/LLd misses after subtracting the
matching preparation path. It also reports:

- packed payload bytes;
- offset-index bytes;
- decoded cache bytes;
- common random-index corpus bytes;
- packed+offset working-set ratio versus one-byte-per-word.

This does not choose a framing/index representation. A future grammar or
compact boundary index may cost less than the host `usize` proxy.

Example:

```bash
python3 benchmarks/pack-efficiency/random_scale.py \
  --binary target/release/examples/pack_efficiency_bench \
  --out /tmp/pack-random \
  --sizes 8,64,1024,65536 \
  --cases w1,d1234,w8 \
  --accesses 4096 --reps 1
```

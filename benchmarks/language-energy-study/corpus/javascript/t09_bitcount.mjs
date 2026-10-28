// T09 bit operations — JavaScript (Node) implementation for the ENERGY-02 corpus.
//
// Two constraints pull in opposite directions and both must hold:
//   1. CORRECTNESS — the LCG must be bit-identical to the reference, so the
//      64-bit state is kept in BigInt (Number would silently drop bits past 2^53
//      and the parity check would compare unequal work).
//   2. SPEED — a per-bit BigInt loop costs ~64 allocations per word, which made
//      MEASURE_SIZE (1e6 words) unmeasurable.
// The fix keeps BigInt only for the state update and counts bits with SWAR on
// two 32-bit halves: exact, and no allocation in the inner loop.
const n = BigInt(process.env.TASK_N);
let x = BigInt(process.env.TASK_SEED);
const MASK = (1n << 64n) - 1n;
const MUL = 6364136223846793005n;
const INC = 1442695040888963407n;

// SWAR popcount for a 32-bit unsigned integer (Hacker's Delight 5-1).
function popcount32(v) {
  v = v - ((v >>> 1) & 0x55555555);
  v = (v & 0x33333333) + ((v >>> 2) & 0x33333333);
  v = (v + (v >>> 4)) & 0x0f0f0f0f;
  return Math.imul(v, 0x01010101) >>> 24;
}

let total = 0;
for (let i = 0n; i < n; i++) {
  x = (x * MUL + INC) & MASK;
  const hi = Number(x >> 32n);
  const lo = Number(x & 0xffffffffn);
  total += popcount32(hi) + popcount32(lo);
}
console.log(String(total));

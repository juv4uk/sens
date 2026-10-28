// T09 bit operations — JavaScript (Node) implementation for the ENERGY-02 corpus.
//
// Reads TASK_N and TASK_SEED from the environment (parity_check.py --run) and
// prints exactly one line: the total popcount.
//
// The LCG is reproduced with BigInt on purpose. JS numbers are doubles and lose
// the low bits past 2^53, so a naive `*` would silently compute a DIFFERENT
// workload — and the parity check would then be comparing unequal work while
// looking green. BigInt keeps the arithmetic bit-identical to the reference.
const n = BigInt(process.env.TASK_N);
let x = BigInt(process.env.TASK_SEED);
const MASK = (1n << 64n) - 1n;
const MUL = 6364136223846793005n;
const INC = 1442695040888963407n;

let total = 0n;
for (let i = 0n; i < n; i++) {
  x = (x * MUL + INC) & MASK;
  let v = x;
  let bits = 0n;
  while (v > 0n) {
    bits += v & 1n;
    v >>= 1n;
  }
  total += bits;
}
console.log(total.toString());

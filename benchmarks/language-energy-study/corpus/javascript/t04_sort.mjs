// T04 sorting — JavaScript (Node) implementation for the ENERGY-02 corpus.
// BigInt is mandatory: JS doubles lose the low bits of 64-bit values, which
// would sort a different array than the reference and still look plausible.
import { createHash } from 'node:crypto';
const n = BigInt(process.env.TASK_N);
let x = BigInt(process.env.TASK_SEED);
const MASK = (1n << 64n) - 1n, MUL = 6364136223846793005n, INC = 1442695040888963407n;
const vals = [];
for (let i = 0n; i < n; i++) { x = (x * MUL + INC) & MASK; vals.push(x); }
vals.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
console.log(createHash('sha256').update(vals.map(String).join(',')).digest('hex'));

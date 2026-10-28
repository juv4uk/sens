// T08 — persistent structure: N appends keeping every version, JavaScript (Node).
// Immutability is modelled by never mutating: each step produces a new array
// via concat, so old versions stay valid. The recorded checkpoints match the
// reference exactly (every 1000 steps, plus the final length).
import { createHash } from 'node:crypto';
const n = Number(process.env.TASK_N);
const marks = [];
let cur = [];
for (let i = 0; i < n; i++) { cur = cur.concat([i]); if (i % 1000 === 0) marks.push(cur.length); }
marks.push(cur.length);
console.log(createHash('sha256').update(marks.join(',')).digest('hex'));

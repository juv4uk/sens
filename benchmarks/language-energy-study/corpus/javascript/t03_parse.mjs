// T03 — parse 'key=value' lines, sort keys, sha256. Same LCG-driven key scheme
// as the reference so both languages see byte-identical input.
import { createHash } from 'node:crypto';
const lines = Number(process.env.TASK_LINES);
const keys = [];
for (let i = 0; i < lines; i++) keys.push('k' + ((i * 7919) % 1000));
keys.sort();
console.log(createHash('sha256').update(keys.join('\n')).digest('hex'));

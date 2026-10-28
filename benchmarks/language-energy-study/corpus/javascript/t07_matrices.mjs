// T07 — NxN matrix product, JavaScript (Node). Contract is TOLERANCE, so the
// output is the numeric sum of all elements, not a hash: a hash would turn a
// tolerance check into a bitwise one and defeat the point of the task.
const n = Number(process.env.TASK_N);
const a = [];
for (let i = 0; i < n; i++) { const row = []; for (let j = 0; j < n; j++) row.push((i + j) % 7 ? 1.0 : 0.5); a.push(row); }
let total = 0.0;
for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) { let s = 0.0; for (let k = 0; k < n; k++) s += a[i][k] * a[k][j]; total += s; }
console.log(total.toFixed(12));

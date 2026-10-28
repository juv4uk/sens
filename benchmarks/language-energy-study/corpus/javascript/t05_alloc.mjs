// T05 — allocation pressure: create and drop N short-lived lists of K items.
const n = Number(process.env.TASK_N), k = Number(process.env.TASK_K);
let total = 0;
for (let i = 0; i < n; i++) { const v = Array.from({ length: k }, (_, j) => j); total += v.length; }
console.log(String(total));

// T01 — naive Fibonacci, JavaScript (Node). Same recursion shape as the reference.
const n = Number(process.env.TASK_N);
function fib(k) { return k < 2 ? k : fib(k - 1) + fib(k - 2); }
console.log(String(fib(n)));

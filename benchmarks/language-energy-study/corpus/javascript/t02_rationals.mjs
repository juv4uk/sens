// T02 — exact sum 1/1 + ... + 1/N as a reduced fraction, JavaScript (Node).
// BigInt is required: the numerator overflows Number long before N=400.
function gcd(a, b) { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) { [a, b] = [b, a % b]; } return a; }
const n = Number(process.env.TASK_N);
let num = 0n, den = 1n;
for (let k = 1; k <= n; k++) {
  const kb = BigInt(k);
  num = num * kb + den;
  den = den * kb;
  const g = gcd(num, den);
  num /= g; den /= g;
}
console.log(num.toString() + '/' + den.toString());

function fib(n: number): number {
  return n < 2 ? n : fib(n - 1) + fib(n - 2);
}

function sieve(n: number): number {
  const comp = new Uint8Array(n + 1);
  for (let i = 2; i * i <= n; i++) {
    if (!comp[i]) {
      for (let j = i * i; j <= n; j += i) comp[j] = 1;
    }
  }
  let count = 0;
  for (let k = 2; k <= n; k++) if (!comp[k]) count++;
  return count;
}

function collatz(n: number): number {
  let total = 0;
  for (let i = 1; i <= n; i++) {
    let x = i;
    while (x !== 1) {
      x = x % 2 === 0 ? x / 2 : 3 * x + 1;
      total++;
    }
  }
  return total;
}

const a = Deno.args;
const fibN = a[0] ? parseInt(a[0]) : 35;
const sieveN = a[1] ? parseInt(a[1]) : 10000000;
const colN = a[2] ? parseInt(a[2]) : 1000000;

console.log(`fib(${fibN}) = ${fib(fibN)}`);
console.log(`sieve(${sieveN}) = ${sieve(sieveN)}`);
console.log(`collatz(${colN}) = ${collatz(colN)}`);

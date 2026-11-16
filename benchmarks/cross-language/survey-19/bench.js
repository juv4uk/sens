function fib(n) {
  return n < 2 ? n : fib(n - 1) + fib(n - 2);
}

function sieve(n) {
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

function collatz(n) {
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

const a = process.argv;
const fibN = a[2] ? parseInt(a[2], 10) : 35;
const sieveN = a[3] ? parseInt(a[3], 10) : 10000000;
const colN = a[4] ? parseInt(a[4], 10) : 1000000;

console.log(`fib(${fibN}) = ${fib(fibN)}`);
console.log(`sieve(${sieveN}) = ${sieve(sieveN)}`);
console.log(`collatz(${colN}) = ${collatz(colN)}`);

const n = Number(process.argv[2] || 200000);
let acc = 0n;
for (let i = 0n; i <= BigInt(n); i++) acc += i * i;
console.log(acc.toString());

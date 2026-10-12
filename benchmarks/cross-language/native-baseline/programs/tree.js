function tree(depth, seed) {
  if (depth === 0) return seed;
  const left = tree(depth - 1, seed * 3n + 1n);
  const right = tree(depth - 1, seed * 3n + 2n);
  return left ^ (right + BigInt(depth));
}
const depth = Number(process.argv[2] || 18);
console.log(tree(depth, 1n).toString());

// T08 — persistent structure with O(1) append, JavaScript (Node).
//
// The previous version used cur = cur.concat([i]), which is O(n) per step and
// therefore O(n^2) overall. That made this task 17x slower than the Python
// reference and would have measured the choice of data structure rather than
// the language. Both sides now build a cons list: a node holds a value and a
// pointer to the previous node, so append is O(1) and every older version stays
// valid because nodes are never mutated.
import { createHash } from 'node:crypto';
const n = Number(process.env.TASK_N);
const marks = [];
let node = null;
let length = 0;
for (let i = 0; i < n; i++) {
  node = { value: i, next: node };
  length += 1;
  if (i % 1000 === 0) marks.push(length);
}
marks.push(length);
console.log(createHash('sha256').update(marks.join(',')).digest('hex'));

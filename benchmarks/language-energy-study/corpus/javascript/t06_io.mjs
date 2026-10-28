// T06 — I/O shape: build the same payload and count bytes and lines.
const lines = Number(process.env.TASK_LINES);
const parts = [];
for (let i = 0; i < lines; i++) parts.push('line-' + String(i).padStart(6, '0'));
const payload = parts.join('\n') + '\n';
console.log(Buffer.byteLength(payload, 'utf8') + ':' + (payload.split('\n').length - 1));

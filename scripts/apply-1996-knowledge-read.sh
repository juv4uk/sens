#!/bin/sh
# Apply #1996 on lib/knowledge.lisp (quoted human read -> Function8 01001010)
set -e
f=lib/knowledge.lisp
test -f "$f"
sed -i \
  -e 's/(00100111 (00000001 read) (00100111 (00000001 tcp-read-to-eof) connection ""))/(00100111 (00000001 01001010) (00100111 (00000001 tcp-read-to-eof) connection ""))/' \
  -e 's/(00100111 (00000001 read) (00100111 (00000001 tcp-read-frame) connection ""))/(00100111 (00000001 01001010) (00100111 (00000001 tcp-read-frame) connection ""))/' \
  "$f"
if grep -n '00100111 (00000001 read)' "$f"; then
  echo 'still has quoted read heads' >&2
  exit 1
fi
echo "#1996 applied on $f"

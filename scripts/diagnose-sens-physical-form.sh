#!/usr/bin/env bash
# Зв'язок індексу фізичної форми з рядком Lisp. Лише діагностика, не оракул.
set -euo pipefail
if (( $# != 3 )); then echo "usage: $0 SOURCE.lisp PAIRED.stderr WITNESS_ID" >&2; exit 2; fi
source="$1"; log="$2"; witness="$3"
[[ -f "$source" && ! -L "$source" && -f "$log" ]] || exit 2
index="$(grep -oEm1 'physical_form_index=[0-9]+' "$log" || true)"
if [[ -z "$index" ]]; then
 echo "SENS_FORM_LOCATION id=$witness physical_form_index=NOT_REPORTED status=NOT_ASSERTED"
 exit 0
fi
index="${index#physical_form_index=}"
# AWK — лексичний пошук лише топ-рівневих дужок поза коментарями та рядками.
awk -v target="$index" -v witness="$witness" '
 BEGIN { depth=0; in_string=0; escaped=0; n=0; found=0 }
 {
  line=$0
  for (i=1; i<=length(line); i++) {
   c=substr(line,i,1)
   if (in_string) {
    if (escaped) { escaped=0; continue }
    if (c=="\\") { escaped=1; continue }
    if (c=="\"") { in_string=0; continue }
    continue
   }
   if (c==";") break
   if (c=="\"") { in_string=1; continue }
   if (c=="(") {
    if (depth==0) {
     if (n==target) {
      found=1
      from=NR
      excerpt=substr(line,i,170)
      gsub(/[\t\r]/," ",excerpt)
     }
     n++
    }
    depth++
   } else if (c==")") {
    depth--
    if (depth<0) {
     printf "SENS_FORM_LOCATION id=%s status=LEXICAL_UNBALANCED line=%d\n", witness, NR
     exit 2
    }
   }
  }
 }
 END {
  if (depth!=0 || in_string) {
   printf "SENS_FORM_LOCATION id=%s status=LEXICAL_UNBALANCED depth=%d string=%d\n", witness, depth, in_string
   exit 2
  }
  if (!found) {
   printf "SENS_FORM_LOCATION id=%s physical_form_index=%s status=INDEX_OUT_OF_RANGE lexical_form_count=%d\n", witness, target, n
   exit 3
  }
  printf "SENS_FORM_LOCATION id=%s physical_form_index=%s source_line=%d lexical_form_count=%d scope=diagnostic-not-semantic\n", witness, target, from, n
  printf "SENS_FORM_SOURCE id=%s first_line=%s\n", witness, excerpt
 }
' "$source"

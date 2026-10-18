; #990 — four-island execution evidence subordinate to Canon()/function table.
;
; Історичний SID8:00001100 був PLUS, не D8:00001100 (зменшити-на-1).
; Чинна ратифікована функція додавання: D5:01010, укр додати.
; Це лише свідчення механізмів, не нова семантична identity.
;
; Reuses (2000+ surface):
;   lib/surface/semantic-registry.lisp (authority),
;   lib/function-table-mechanisms.lisp (mechanism-source),
;   mechanism-select / island-lowering consumers of these rows.
;
; This is NOT a semantic contract and must not carry operation names, law or
; domain. Semantic identity/meaning stays in lib/surface/semantic-registry.lisp
; and #1046. Evidence donors: closed #1042 (executor observations), #1052
; (Datalog replay). Current bounded slice: SID 00001100 only, because #1053
; already admits all four executor routes for that existing SID. Final semantic
; ratification remains blocked until law/domain are available from the one
; Canon/function-table authority row.
;
; Чотири історичні executor-свідки SID8:00001100 тепер посилаються на
; ратифіковану українську проєкцію D5:01010. D8:00001100 — інша функція.
; Не ототожнювати однакові 8-бітні записи між епохами і доменами.

(
  (schema island-math-evidence/1)
  (authority "lib/surface/semantic-registry.lisp")
  (role mechanism-evidence-only)
  (parent-issue 990)
  (canon-convergence-issue 1046)
  (mechanism-source "lib/function-table-mechanisms.lisp")
  (ratification-state blocked-until-canon-law-domain)
  (rows
    (додати common-lisp execution-witness "#1042-donor")
    (додати prolog execution-witness "#1042-donor")
    (додати clips execution-witness "#1042-donor")
    (додати datalog execution-witness "#1052-replay+#1042-donor")))

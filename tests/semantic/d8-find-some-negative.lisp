; Wrong-result orientation: FIND 'б' in ('а' 'б') must NOT return 'а'.
(equal?
  (знайти-перший-збіг (quote б) (list (quote а) (quote б)))
  (quote а))

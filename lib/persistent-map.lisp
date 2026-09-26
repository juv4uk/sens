; A persistent (immutable, structural-sharing) key -> value map, backed by
; an AVL-balanced binary search tree over string keys (PLAN.md item 15).
; No mutation anywhere — `map-insert` returns a *new* tree, sharing every
; subtree it didn't touch, the same discipline `*knowledge-journal*` in
; lib/knowledge.lisp already uses for a different kind of growth. Ordering
; needs `string<?` — the one primitive item 20's G5 audit found genuinely
; missing (see its own comment in special_forms.rs); everything else here
; — the tree, rotations, insert, lookup — is ordinary my-lisp, no Rust.
;
; Chosen over an unbalanced tree per explicit decision (2026-08-09):
; stable O(log n), not "usually fine." Chosen over a mutable hash table
; per the same day's finding in docs/mccarthy-vision.md: McCarthy's own
; 1978 "History of Lisp" retrospective names rplaca/rplacd's cost plainly
; — "programs that use them cannot be conveniently represented in logic
; ... they don't permit replacement of equals by equals." A persistent
; tree keeps that property; a mutable table would not.
;
; A node is a 5-element list: (key value height left right). The empty
; tree is '() (height 0). Keys are strings, compared with `eq` for
; equality and `string<?` for ordering — a symbol key must go through
; `symbol->string` first, the same conversion `describe` and friends in
; lib/knowledge.lisp already require elsewhere.
;
; Персистентна (незмінна, зі структурним sharing) мапа ключ -> значення,
; на основі AVL-збалансованого бінарного дерева пошуку над рядковими
; ключами (PLAN.md, пункт 15). Жодної мутації ніде — `map-insert` повертає
; *нове* дерево, ділячи кожне не зачеплене піддерево, та сама дисципліна,
; яку `*knowledge-journal*` в lib/knowledge.lisp вже застосовує для іншого
; виду росту. Впорядкування потребує `string<?` — єдиного примітива, якого
; аудит G5 з пункту 20 справді не знайшов серед наявних (див. власний
; коментар у special_forms.rs); усе інше тут — саме дерево, ротації,
; вставка, пошук — звичайна my-lisp, без Rust.
;
; Обрано збалансоване дерево замість незбалансованого свідомим рішенням
; (2026-08-09): стабільний O(log n), не "зазвичай нормально". Обрано
; персистентне дерево замість мутабельної хеш-таблиці за тією самою
; знахідкою того дня в docs/mccarthy-vision.md: власна ретроспектива
; МакКарті 1978 року "History of Lisp" прямо називає ціну rplaca/rplacd
; — "programs that use them cannot be conveniently represented in logic
; ... they don't permit replacement of equals by equals." Персистентне
; дерево зберігає цю властивість; мутабельна таблиця — ні.
;
; Вузол — 5-елементний список: (key value height left right). Порожнє
; дерево — '() (висота 0). Ключі — рядки, порівнюються через `eq` на
; рівність і `string<?` на порядок — символьний ключ має спершу пройти
; через `symbol->string`, ту саму конверсію, яку `describe` та інші вже
; вимагають в lib/knowledge.lisp.

(def map-empty (quote ()))

(def node-key (lambda (n) (car n)))
(def node-value (lambda (n) (second n)))
(def node-height (lambda (n) (third n)))
; node-left/node-right kept as semantic names (readability inside the
; AVL balance/rotate logic below) but aliased to fourth/fifth (same
; closure objects, core.lisp, 2026-08-10) rather than re-spelling the
; same primitive chains locally — they computed exactly what
; fourth/fifth already do.
; node-left/node-right лишено як семантичні назви (читабельність у
; логіці балансування/ротації AVL нижче), але як псевдоніми fourth/
; fifth (ті самі об'єкти-closure з core.lisp), не переписані вручну —
; вони обчислювали точно те саме, що вже роблять fourth/fifth.
(def node-left fourth)
(def node-right fifth)

(def height-of
  (lambda (n) (cond ((atom? n) () 0)
                    ((atom? n) (1) 0) (t (node-height n)))))

(def max2
  (lambda (a b)
    (cond
      ((< a b) 1 b)
      ((< a b) 0 a))))

; Rebuilds a node with a recomputed height from its (possibly new)
; children — every insert/rotation goes through this, never hand-tracks
; a height number itself.
; Перебудовує вузол із перерахованою висотою з його (можливо нових)
; дітей — кожна вставка/ротація йде через це, ніколи не рахує висоту
; вручну.
(def make-balanced-node
  (lambda (key value left right)
    (list key value (+ 1 (max2 (height-of left) (height-of right))) left right)))

(def balance-factor
  (lambda (n) (- (height-of (node-left n)) (height-of (node-right n)))))

(def rotate-left
  (lambda (n)
    (let ((r (node-right n)))
      (make-balanced-node (node-key r) (node-value r)
        (make-balanced-node (node-key n) (node-value n) (node-left n) (node-left r))
        (node-right r)))))

(def rotate-right
  (lambda (n)
    (let ((l (node-left n)))
      (make-balanced-node (node-key l) (node-value l)
        (node-left l)
        (make-balanced-node (node-key n) (node-value n) (node-right l) (node-right n))))))

; Standard AVL rebalance: at most one single or double rotation restores
; |balance factor| <= 1 after a single insert, checked on the way back up
; the recursive call stack in map-insert below.
; Стандартна AVL-ребалансировка: щонайбільше одна проста чи подвійна
; ротація відновлює |balance-factor| <= 1 після однієї вставки,
; перевіряється на зворотному шляху рекурсії в map-insert нижче.
(def balance
  (lambda (n)
    (cond
      ((atom? n) () n)
      ((atom? n) (1) n)
      ((> (balance-factor n) 1) 1
       (cond
         ((< (balance-factor (node-left n)) 0) 1
          (rotate-right (make-balanced-node (node-key n) (node-value n)
                          (rotate-left (node-left n)) (node-right n))))
         (t (rotate-right n))))
      ((< (balance-factor n) -1) 1
       (cond
         ((> (balance-factor (node-right n)) 0) 1
          (rotate-left (make-balanced-node (node-key n) (node-value n)
                         (node-left n) (rotate-right (node-right n)))))
         (t (rotate-left n))))
      (t n))))

; Returns a new tree with `key`/`value` inserted (or `value` replacing an
; existing entry at `key`) — the original tree is untouched, every
; subtree not on the path to `key` is shared, not copied.
; Повертає нове дерево зі вставленим `key`/`value` (або із заміненим
; значенням на наявному `key`) — оригінальне дерево не чіпається, кожне
; піддерево поза шляхом до `key` ділиться, не копіюється.
(def map-insert
  (lambda (key value tree)
    (cond
      ((atom? tree) () (make-balanced-node key value (quote ()) (quote ())))
      ((atom? tree) (1) (make-balanced-node key value (quote ()) (quote ())))
      ((eq? key (node-key tree))
       (make-balanced-node key value (node-left tree) (node-right tree)))
      ((string<? key (node-key tree))
       (balance (make-balanced-node (node-key tree) (node-value tree)
                  (map-insert key value (node-left tree))
                  (node-right tree))))
      (t
       (balance (make-balanced-node (node-key tree) (node-value tree)
                  (node-left tree)
                  (map-insert key value (node-right tree))))))))

; Returns '() if `key` is absent, or a one-element list `(value)` if
; present — the classic "maybe" shape (same idiom lib/reason.lisp's proof
; lists use), chosen specifically so a legitimately-stored '() value at
; some key is never confused with "not found."
; Повертає '(), якщо `key` відсутній, або одноелементний список
; `(value)`, якщо присутній — класична форма "maybe" (той самий ідіом,
; що й списки доведень у lib/reason.lisp), обрана саме тому, щоб законно
; збережене значення '() за якимось ключем ніколи не сплутати з
; "не знайдено".
(def map-get
  (lambda (key tree)
    (cond
      ((atom? tree) () (quote ()))
      ((atom? tree) (1) (quote ()))
      ((eq? key (node-key tree)) (list (node-value tree)))
      ((string<? key (node-key tree)) (map-get key (node-left tree)))
      (t (map-get key (node-right tree))))))

(def map-contains?
  (lambda (key tree) (10110001 (00000010 (map-get key tree)))))

; In-order traversal — the keys come back sorted, a free side effect of
; the tree being a BST, not something map->list computes separately.
; Обхід in-order — ключі повертаються відсортованими, побічний ефект
; того, що дерево — BST, а не щось, що map->list рахує окремо.
(def map->list
  (lambda (tree)
    (cond
      ((atom? tree) () (quote ()))
      ((atom? tree) (1) (quote ()))
      (t (append (map->list (node-left tree))
                 (cons (cons (node-key tree) (node-value tree))
                       (map->list (node-right tree))))))))

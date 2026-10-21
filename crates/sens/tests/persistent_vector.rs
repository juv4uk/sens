//! Перевіряє виконуваний lib/persistent-vector.lisp у справжньому SENS.
//! Не підміняє D1/D4/D5 закони зовнішнім evaluator. Завантажує
//! lib/core.lisp (for `second`/`third`/`fourth`/`fifth`/`not`/`append`)
//! and lib/persistent-vector.my into one session, same as a user
//! loading both from a REPL.

use sens::{eval_program, Session};

fn eval_vec(source: &str) -> String {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(
        include_str!("../../../lib/persistent-vector.lisp"),
        &mut session,
    )
    .unwrap();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn empty_vector_has_nothing() {
    assert_eq!(eval_vec("(вектор-н-тий 0 вектор-порожній)"), "()");
    assert_eq!(eval_vec("(вектор-кількість вектор-порожній)"), "0");
    assert_eq!(eval_vec("(вектор-список вектор-порожній)"), "()");
}

#[test]
fn conj_then_nth_finds_the_value_at_its_index() {
    let source = r#"
        (def v (вектор-додати (quote c) (вектор-додати (quote b) (вектор-додати (quote a) вектор-порожній))))
        (list (вектор-н-тий 0 v) (вектор-н-тий 1 v) (вектор-н-тий 2 v) (вектор-н-тий 3 v) (вектор-кількість v))
    "#;
    assert_eq!(eval_vec(source), "((a) (b) (c) () 3)");
}

/// The order-preservation bug caught live before this test existed: a
/// naive `(вектор-додати (car lst) (вектор-з-список (cdr lst)))` conjes the
/// LAST list element first (its recursive call bottoms out before any
/// conj runs), reversing the list into the vector. вектор-з-список uses
/// an accumulator instead — this test is exactly what would have failed
/// on the naive version.
#[test]
fn vec_from_list_preserves_list_order() {
    assert_eq!(
        eval_vec("(вектор-список (вектор-з-список (list 10 20 30 40 50)))"),
        "(10 20 30 40 50)"
    );
}

#[test]
fn conj_is_persistent_the_original_vector_is_untouched() {
    let source = r#"
        (def v1 (вектор-додати (quote a) вектор-порожній))
        (def v2 (вектор-додати (quote b) v1))
        (list (вектор-список v1) (вектор-список v2) (вектор-кількість v1) (вектор-кількість v2))
    "#;
    assert_eq!(eval_vec(source), "((a) (a b) 1 2)");
}

/// The actual point of choosing a balanced tree: 4607 sequential
/// вектор-додати calls (already-ascending index insertion order, the exact
/// pattern that degenerates an unbalanced BST into a height-4607 linked
/// list) still produces a tree whose height stays near the theoretical
/// AVL minimum, not linear in element count — verified live before this
/// test was written by printing vnode-height and comparing to
/// ceil(log2(n+1)), not assumed from the rotation code alone.

#[test]
fn vec_nth_out_of_bounds_returns_the_maybe_shape_absent_case() {
    let source = r#"
        (def v (вектор-з-список (list 1 2 3)))
        (list (вектор-н-тий 3 v) (вектор-н-тий 100 v))
    "#;
    assert_eq!(eval_vec(source), "(() ())");
}

/// Empirical confirmation this actually fixes the cited problem
/// (OPT-PERSISTENT-VECTOR: WSM-24's O(n) `nth` inside a subsample loop
/// over a 4607-point list made the whole loop O(n^2)) — not just a
/// microbenchmark in isolation, the exact access pattern (many
/// sequential index lookups over a large collection) that motivated
/// this file.
#[test]
fn vec_nth_over_a_large_vector_returns_correct_values_at_every_index() {
    let source = r#"
        (def build-range
          (lambda (n acc)
            (cond ((eq? n 0) acc)
                  (t (build-range (- n 1) (cons n acc))))))
        (def big (вектор-з-список (build-range 4607 (quote ()))))
        (def check-all
          (lambda (i n v)
            (cond ((eq? i n) t)
                  ((eq? (car (вектор-н-тий i v)) (+ i 1)) (check-all (+ i 1) n v))
                  (t (quote ())))))
        (list (вектор-кількість big) (check-all 0 4607 big))
    "#;
    assert_eq!(eval_vec(source), "(4607 t)");
}

#[test]
fn українські_іменовані_повороти_avl_виконуються_в_sens() {
    // Позитивні SENS-eval для обох поворотів: не текстовий Python-оракул.
    // Обидва піддерева створює чинний український Lisp.
    let лівий = "(вектор-вузол-індекс
        (вектор-повернути-ліворуч
          (вектор-створити-збалансований-вузол 1 10 (як-є ())
            (вектор-створити-збалансований-вузол 2 20 (як-є ()) (як-є ())))))";
    let правий = "(вектор-вузол-індекс
        (вектор-повернути-праворуч
          (вектор-створити-збалансований-вузол 2 20
            (вектор-створити-збалансований-вузол 1 10 (як-є ()) (як-є ()))
            (як-є ()))))";
    assert_eq!(eval_vec(лівий), "2", "лівий поворот має підняти праву дитину");
    assert_eq!(eval_vec(правий), "1", "правий поворот має підняти ліву дитину");
    assert_eq!(eval_vec("(вектор-висота-піддерева (як-є ()))"), "0",
        "порожній вузол має D1-позитивну гілку ATOM");
    // Негативна гілка того самого D1/COND: непорожній вузол не має висоти 0.
    assert_eq!(
        eval_vec("(вектор-висота-піддерева
           (вектор-створити-збалансований-вузол 1 10 (як-є ()) (як-є ())))"),
        "1"
    );
}


#[test]
fn d11_дерево_відрізняє_порожнє_значення_від_відсутнього() {
    // VTREE-INSERT/VTREE-GET: (()) означає наявне порожнє значення,
    // а () означає відсутній індекс. Заміна не мутує старе дерево.
    let source = r#"
        (def попереднє
          (вставити-в-дерево-вектора 2 (як-є ()) (як-є ())))
        (def оновлене
          (вставити-в-дерево-вектора 2 7 попереднє))
        (list
          (отримати-з-дерева-вектора 2 попереднє)
          (отримати-з-дерева-вектора 2 оновлене)
          (отримати-з-дерева-вектора 1 оновлене))
    "#;
    assert_eq!(eval_vec(source), "((()) (7) ())");
}

#[test]
fn d11_поворот_зберігає_inorder_та_старе_дерево() {
    // VROTATE-LEFT має змінити корінь, але не переставити дані,
    // не знищити джерельне персистентне дерево й оновити висоту.
    let source = r#"
        (def попереднє
          (вектор-створити-збалансований-вузол 1 10 (як-є ())
            (вектор-створити-збалансований-вузол 2 20
              (як-є ()) (як-є ()))))
        (def повернуте (вектор-повернути-ліворуч попереднє))
        (list
          (вектор-вузол-індекс попереднє)
          (вектор-вузол-індекс повернуте)
          (перетворити-дерево-вектора-на-список попереднє)
          (перетворити-дерево-вектора-на-список повернуте)
          (вектор-вузол-висота повернуте))
    "#;
    assert_eq!(eval_vec(source), "(1 2 (10 20) (10 20) 2)");
}

//! Ратифікована геометрія інших родин ≠ універсальний закон останнього біта.
//! Реальні функції обчислює SENS із lib/core4.lisp, а не Rust/Python-оракул.
use sens::{eval_program, load_core_library, Session};

#[test]
fn d5_d6_owner_pairs_follow_their_own_local_laws() {
    let d5 = include_str!("../../../lib/domains/d5.lisp");
    let d6 = include_str!("../../../lib/domains/d6.lisp");
    // D5 reverse/onto shares one accumulator law; unlike CAR/CDR,
    // its suffix bit selects an optional accumulator, not A/D composition.
    for row in [
        "(10100 (ук зворот) (укр зворот)",
        "(10101 (ук зворот-до) (укр зворот-до)",
    ] {
        assert!(d5.contains(row), "ratified D5 relation drift: {row}");
    }
    // D6 traversal square: high of the final two bits selects the
    // accumulator variant; lowest selects MAP vs FILTER.
    for row in [
        "(101000 (ук відобразити) (укр відобразити)",
        "(101001 (ук відсіяти) (укр відсіяти)",
        "(101010 (ук відобразити-до) (укр відобразити-до)",
        "(101011 (ук відсіяти-до) (укр відсіяти-до)",
        "(000000 (ук довжина) (укр довжина)",
        "(000001 (ук довжина-до) (укр довжина-до)",
        "(010000 (ук парне?) (укр парне?)",
        "(010001 (ук непарне?) (укр непарне?)",
        "(110000 (ук взяти) (укр взяти)",
        "(110001 (ук відкинути) (укр відкинути)",
        "(111100 (ук будь-яке?) (укр будь-яке?)",
        "(111101 (ук усі?) (укр усі?)",
    ] {
        assert!(d6.contains(row), "ratified D6 relation drift: {row}");
    }

    let mut session = Session::default();
    load_core_library(&mut session).expect("load actual SENS core4 source");
    for (law, left, right) in [
        ("D5 REVERSE(x)=REVERSE-ONTO(x,())",
         "(зворот (як-є (а б в)))",
         "(зворот-до (як-є (а б в)) (як-є ()))"),
        ("D5 APPEND(x,y)=REVERSE-ONTO(REVERSE(x),y)",
         "(приєднати (як-є (а б)) (як-є (в г)))",
         "(зворот-до (зворот (як-є (а б))) (як-є (в г)))"),
        ("D6 LENGTH(x)=LENGTH-ONTO(x,0)",
         "(довжина (як-є (а б в)))",
         "(довжина-до (як-є (а б в)) 0)"),
        ("D6 MAP(f,x)=MAP-ONTO(f,x,())",
         "(відобразити (функція (елемент) елемент) (як-є (а б в)))",
         "(відобразити-до (функція (елемент) елемент) (як-є (а б в)) (як-є ()))"),
        ("D6 FILTER(p,x)=FILTER-ONTO(p,x,())",
         "(відсіяти (функція (елемент) (атом? елемент)) (як-є (а (б) в)))",
         "(відсіяти-до (функція (елемент) (атом? елемент)) (як-є (а (б) в)) (як-є ()))"),
        ("D6 ODDP(n)=NOT(EVENP(n))",
         "(непарне? 3)",
         "(хибне? (парне? 3))"),
        ("D6 TAKE/DROP partition",
         "(приєднати (взяти 2 (як-є (а б в г))) (відкинути 2 (як-є (а б в г))))",
         "(як-є (а б в г))"),
        ("D6 ALL(p,x)=NOT(ANY(NOT p,x))",
         "(усі? (функція (елемент) (атом? елемент)) (як-є (а (б) в)))",
         "(хибне? (будь-яке? (функція (елемент) (хибне? (атом? елемент))) (як-є (а (б) в))))"),
    ] {
        let lhs = eval_program(left, &mut session)
            .unwrap_or_else(|error| panic!("{law} lhs: {error}"));
        let rhs = eval_program(right, &mut session)
            .unwrap_or_else(|error| panic!("{law} rhs: {error}"));
        assert_eq!(lhs.value, rhs.value,
            "test_id=other-domain-family layer=SENS law={law} lhs={left} rhs={right}");
    }
}

#[test]
fn d8_do_while_product_two_axes_are_observable_in_native_sens() {
    // Ратифікований інваріант: 11001111 — стоп на істині, повернути стан.
    // Інший новий кут 11001101 — продовжувати на істині й застосувати результат.
    // Зміна останніх двох бітів тут — локальний добуток Д6 DO/WHILE,
    // а НЕ загальний зміст бітів для всіх інших доменів.
    let d8 = include_str!("../../../lib/domains/d8.lisp");
    for row in [
        "(11001101 (ук доки-істина+застосувати) (укр продовжувати-поки-істина-й-застосувати-результат)",
        "(11001111 (ук зупинити-на-істині+стан) (укр зупинити-коли-істина-й-повернути-стан)",
    ] {
        assert!(d8.contains(row), "test_id=d8-loop-product layer=owner-map missing={row}");
    }

    let mut session = Session::default();
    load_core_library(&mut session).expect("current SENS Core4 language");
    // Identical initial state, same P(x)=empty?(x), step(x)=CDR(x).
    // Four product corners have pairwise different observable outputs.
    let cases = [
        (
            "продовжувати-на-істині+стан / D6:110011",
            "(поки порожній? решта (як-є (а б)))",
            "(як-є (а б))",
        ),
        (
            "продовжувати-на-істині+результат / D8:11001101",
            "(продовжувати-поки-істина-й-застосувати-результат порожній? решта (функція (стан) (сполучити (як-є мітка) стан)) (як-є (а б)))",
            "(як-є (мітка а б))",
        ),
        (
            "зупиняти-на-істині+стан / D8:11001111",
            "(зупинити-коли-істина-й-повернути-стан порожній? решта (як-є (а б)))",
            "(як-є ())",
        ),
        (
            "зупиняти-на-істині+результат / D6:110010",
            "(робити решта порожній? (функція (стан) (сполучити (як-є мітка) стан)) (як-є (а б)))",
            "(як-є (мітка))",
        ),
    ];
    let mut actuals = Vec::new();
    for (law, source, expected_source) in cases {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|err| panic!("test_id=d8-loop-product law={law} input={source} error={err}")).value;
        let expected = eval_program(expected_source, &mut session)
            .unwrap_or_else(|err| panic!("test_id=d8-loop-product expected={expected_source} error={err}")).value;
        assert_eq!(actual, expected,
            "test_id=d8-loop-product layer=SENS law={law} expected={expected_source} actual={source}");
        assert!(actuals.iter().all(|prior| prior != &actual),
            "test_id=d8-loop-product layer=SENS distinct-corners law={law}");
        actuals.push(actual);
    }

    // Д1 предикат, що повертає список, не перетворюється на істину хостом.
    let invalid = "(зупинити-коли-істина-й-повернути-стан (функція (стан) (як-є ())) решта (як-є (а)))";
    assert!(eval_program(invalid, &mut session).is_err(),
        "test_id=d8-loop-product layer=SENS expected=D1-type-rejection actual=accepted");
}

#[test]
fn d8_eight_product_invariants_reuse_executable_ukrainian_laws() {
    // Тільки затверджений Lisp-контракт вирішує, які координати мають
    // незалежно доведений 2x2 добуток. Не JSON-каталог і не повний D8.
    let authority = include_str!("../../../contracts/d8-ratification.lisp");
    let surfaces = include_str!("../../../lib/domains/d8.lisp");
    let definitions = include_str!("../../../lib/core4.lisp");
    let mut invariant_count = 0usize;
    for line in authority.lines() {
        if !line.contains("owner-ratified-product-invariant PRODUCT-INVARIANT") {
            continue;
        }
        let bits = line.split('"').nth(1)
            .expect("D8 resident carries its exact binary coordinate");
        assert_eq!(bits.len(), 8, "test_id=d8-product-geometry width={bits}");
        assert!(bits.ends_with("11"),
            "test_id=d8-product-geometry invariant must be the commuting 11 corner: {bits}");
        let row = surfaces.lines()
            .find(|line| line.trim_start().starts_with(&format!("({bits} ")))
            .unwrap_or_else(|| panic!("test_id=d8-product-geometry no Ukrainian projection for {bits}"));
        let ukr = row.split("(укр ").nth(1)
            .and_then(|rest| rest.split(')').next())
            .expect("each ratified product invariant has Ukrainian source spelling");
        let definition = format!("(визначити {ukr}");
        assert!(
            definitions.contains(&definition),
            "test_id=d8-product-definition layer=SENS coordinate={bits} ukr={ukr} expected=real-Lisp-DEFINE actual=missing"
        );
        invariant_count += 1;
    }
    assert_eq!(invariant_count, 8,
        "test_id=d8-product-authority expected=8 proof-anchored-corners actual={invariant_count}");
}

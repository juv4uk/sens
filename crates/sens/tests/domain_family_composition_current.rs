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
    ] {
        let lhs = eval_program(left, &mut session)
            .unwrap_or_else(|error| panic!("{law} lhs: {error}"));
        let rhs = eval_program(right, &mut session)
            .unwrap_or_else(|error| panic!("{law} rhs: {error}"));
        assert_eq!(lhs.value, rhs.value,
            "test_id=other-domain-family layer=SENS law={law} lhs={left} rhs={right}");
    }
}

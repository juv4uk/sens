//! Temporary native stage investigation. No semantics changed.
#![cfg(all(target_os = "linux", target_arch = "x86_64"))]
use sens::{eval_program, load_core_library, Session};
use std::fs;
fn main() {
    sens_host::install();
    let mut session = Session::default();
    if let Err(e) = load_core_library(&mut session) {
        println!("CORE BLOCKED {e:?}"); return;
    }
    for path in [
        "lib/machine/layout/pair-x86-64.lisp",
        "lib/machine/encoding/x86-64.lisp",
        "lib/machine/admission/x86-64.lisp",
        "lib/machine/lowering/semantic-x86-64.lisp",
    ] {
        let src = fs::read_to_string(path).unwrap();
        if let Err(e) = eval_program(&src, &mut session) {
            println!("LOAD BLOCKED {path}: {e:?}"); return;
        }
        println!("LOAD PASS {path}");
    }
    let checks = [
        ("reference", "(перше (сполучити 2 3))"),
        // Isolate the exact expression that fails in native CAR/CDR. The
        // first failing row now distinguishes lowerer binding from admission.
        ("pair-store", "(x86-lower-bounded-pair-store-u64-forms 2 3)"),
        ("pair-store-alias", "(x86-lower-bounded-pair-store-u64-instructions 2 3)"),
        // Ізолюємо композицію списків від машинного admission.
        ("зворот-списку", "(00101010 (00000001 (a b)))"),
        ("приєднання-списків", "(00101001 (00000001 (a b)) (00000001 (c d)))"),
        ("доповнення-предиката", "(0100 (00000010 (00000001 (a b))))"),
        // Розбиваємо допуск uimm8 на перевірку джерельних числових носіїв.
        ("числовий-дріт", "(01001100 4)"),
        // Ділимо залежності парсера числового дроту до примітивних клітин.
        ("порожній-текст", "(00111100 \"\")"),
        ("непорожній-текст", "(00111100 \"100/1\")"),
        ("перший-символ-тексту", "(00111111 \"100/1\")"),
        ("хвіст-тексту", "(01000000 \"100/1\")"),
        ("рівність-символів", "(00000011 \"1\" \"1\")"),
        // Чи окремі порівняння мають свій точний D1 вихід?
        ("порівняння-не-менше", "(00011110 4 0)"),
        ("порівняння-не-більше", "(00011101 4 255)"),
        ("знаменник-одиниця", "(x86-admission-wire-denominator-one? \"#q2:4/1\")"),
        ("цілочисельність", "(x86-admission-exact-integer? 4)"),
        ("число-в-межах", "(x86-admission-within-inclusive-integer-range? 4 0 255)"),
        ("forms", "(x86-lower-cons-car-u64-forms 2 3)"),
        // Exercise the uimm8 wildcard path directly; the original MOV-only
        // pattern check did not traverse this predicate path.
        ("uimm8-predicate", "(x86-admission-uimm8? 4)"),
        ("uimm8-pattern", "(x86-admission-pattern-match? (00000001 (shl-r64-imm8 register uimm8)) (00000001 (shl-r64-imm8 rax 4)))"),
        ("uimm8-admission", "(x86-admitted-instruction? (00000001 (shl-r64-imm8 rax 4)))"),
        ("uimm8-encode", "(x86-encode-admitted-instruction (00000001 (shl-r64-imm8 rax 4)))"),
        ("pattern-direct", "(x86-admission-pattern-match? (00000001 (mov-r64-imm64 register immediate)) (00000001 (mov-r64-imm64 rax 2)))"),
        ("admit-one", "(x86-admitted-instruction? (00000001 (mov-r64-imm64 rax 2)))"),
        ("admit-ret", "(x86-admitted-instruction? (00000001 (ret)))"),
        ("admit-program", "(x86-admitted-program? (x86-lower-cons-car-u64-forms 2 3))"),
        ("encode-one", "(x86-encode-admitted-instruction (00000001 (ret)))"),
        ("encode-program", "(x86-encode-admitted-program (x86-lower-cons-car-u64-forms 2 3))"),
        ("native-call", "(x86-call-admitted-u64 (x86-lower-cons-car-u64-forms 2 3) x86-pair-cell-bytes)"),
    ];
    for (name, source) in checks {
        match eval_program(source, &mut session) {
            Ok(res) => println!("STAGE PASS {name} = {}", res.value),
            Err(err) => println!("STAGE BLOCKED {name}: {err:?}"),
        }
    }
}

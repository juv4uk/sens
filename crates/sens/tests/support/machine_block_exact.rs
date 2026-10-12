use sens::{eval_parsed_expressions, parse_mixed_exact_domain_machine_source, Session};

const SOURCE: &str = include_str!("../../../../lib/machine/block-exact.lisp");
const PATH: &str = "lib/machine/block-exact.lisp";

pub fn load(session: &mut Session) {
    let forms = parse_mixed_exact_domain_machine_source(PATH, SOURCE)
        .expect("машинний блок має зберігати точні D3/D4-голови");
    eval_parsed_expressions(&forms, session)
        .expect("шість функцій машинного блока мають визначитися за D3/D4");
}

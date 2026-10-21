//! Emit whole-source AST counts for the current Ukrainian Lisp projection.
//! The physical T5M byte count is collected only after the Zig CLI mint step.

use sens::{parse, source_projection, Expr, ExprKind};
use std::{env, fs, process};

fn count_expr(expression: &Expr) -> usize {
    let children = match &expression.kind {
        ExprKind::List(items) | ExprKind::Call(_, items) | ExprKind::DomainCall(_, items) => {
            items.iter().map(count_expr).sum()
        }
        ExprKind::Pair(head, tail) => count_expr(head) + count_expr(tail),
        _ => 0,
    };
    1 + children
}

fn count_program(expressions: &[Expr]) -> usize {
    expressions.iter().map(count_expr).sum()
}

fn run() -> Result<(), String> {
    let path = env::args()
        .nth(1)
        .ok_or("usage: program_size <program.lisp>")?;
    let source = fs::read_to_string(&path).map_err(|error| format!("read {path}: {error}"))?;
    let parsed = parse(&source).map_err(|error| format!("SENS parse: {error:?}"))?;
    let projected = source_projection::project_ukr_decimal_integer_literals(&parsed, &source)
        .map_err(|error| format!("SENS decimal projection: {error:?}"))?;
    let lowered = sens::lower_program(&projected);

    println!("FORMS={}", projected.len());
    println!("SOURCE_BYTES={}", source.len());
    println!("AST_NODES={}", count_program(&projected));
    println!("LOWERED_AST_NODES={}", count_program(&lowered));
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("program_size: {error}");
        process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn counts_every_node_across_all_top_level_forms() {
        let expressions = parse("(а б)\n(в)").expect("parse two source forms");
        assert_eq!(expressions.len(), 2);
        assert_eq!(count_program(&expressions), 5);
    }

    #[test]
    fn decimal_projection_preserves_full_program_ast_shape() {
        let source = "(додати 20 22)\n(відняти 9 7)";
        let parsed = parse(source).expect("parse Ukrainian decimal source");
        let projected = source_projection::project_ukr_decimal_integer_literals(&parsed, source)
            .expect("project decimals into exact SENS numeric words");
        assert_eq!(count_program(&parsed), count_program(&projected));
        assert_eq!(projected.len(), 2);
    }
}

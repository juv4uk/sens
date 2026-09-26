use sens::{
    installed_capabilities, parse, semantic_registry_export, Expr, ExprKind, Sens8,
};
use std::collections::HashSet;
use std::env;
use std::fs;
use std::process;

#[derive(Clone, Debug, Eq, PartialEq)]
struct Edit {
    start: usize,
    end: usize,
    replacement: String,
}

#[derive(Default, Debug)]
struct Analysis {
    edits: Vec<Edit>,
    named_calls: usize,
    blocked_host_capabilities: usize,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum HeadKind {
    Quote,
    Cond,
    Lambda,
    Define,
    Defmacro,
    Let,
    LetStar,
    Other,
}

fn head_kind(sens: Sens8) -> HeadKind {
    if sens == sens::sens!(00000001) {
        HeadKind::Quote
    } else if sens == sens::sens!(00000111) {
        HeadKind::Cond
    } else if sens == sens::sens!(00001000) {
        HeadKind::Lambda
    } else if sens == sens::sens!(00001001) || sens == sens::sens!(00001011) {
        HeadKind::Define
    } else if sens == sens::sens!(00001010) {
        HeadKind::Defmacro
    } else if sens == sens::sens!(10011100) {
        HeadKind::Let
    } else if sens == sens::sens!(10011101) {
        HeadKind::LetStar
    } else {
        HeadKind::Other
    }
}

fn target_sens(sens: Sens8) -> Sens8 {
    if sens == sens::sens!(00001011) {
        sens::sens!(00001001)
    } else {
        sens
    }
}

fn host_capability_names() -> HashSet<String> {
    sens_host::install();
    installed_capabilities().into_iter().collect()
}

fn resolve_head<'a>(
    head: &'a Expr,
    bound: &HashSet<String>,
    host_capabilities: &HashSet<String>,
    analysis: &mut Analysis,
) -> Option<(Option<&'a str>, Sens8)> {
    match &head.kind {
        ExprKind::Sid(sens) => Some((None, *sens)),
        ExprKind::Symbol(name) if !bound.contains(name.as_ref()) => {
            if host_capabilities.contains(name.as_ref()) {
                if semantic_registry_export::semantic_id_for_admitted_surface(name).is_some() {
                    analysis.blocked_host_capabilities += 1;
                }
                return None;
            }
            semantic_registry_export::semantic_id_for_admitted_surface(name)
                .map(|sens| (Some(name.as_ref()), sens))
        }
        _ => None,
    }
}

fn push_head_edit(head: &Expr, sens: Sens8, analysis: &mut Analysis) {
    analysis.edits.push(Edit {
        start: head.span.start,
        end: head.span.end,
        replacement: target_sens(sens).to_string(),
    });
}

fn collect_parameter_names(expression: &Expr, out: &mut HashSet<String>) {
    match &expression.kind {
        ExprKind::Symbol(name) => {
            out.insert(name.to_string());
        }
        ExprKind::List(items) => {
            for item in items.iter() {
                collect_parameter_names(item, out);
            }
        }
        ExprKind::Pair(head, tail) => {
            collect_parameter_names(head, out);
            collect_parameter_names(tail, out);
        }
        _ => {}
    }
}

fn walk_sequence(
    expressions: &[Expr],
    bound: &mut HashSet<String>,
    host_capabilities: &HashSet<String>,
    analysis: &mut Analysis,
    top_level: bool,
) {
    for expression in expressions {
        walk_expr(
            expression,
            bound,
            host_capabilities,
            analysis,
            top_level,
        );
    }
}

fn walk_cond_clauses(
    arguments: &[Expr],
    bound: &HashSet<String>,
    host_capabilities: &HashSet<String>,
    analysis: &mut Analysis,
) {
    for clause in arguments {
        match &clause.kind {
            ExprKind::List(parts) => {
                let mut clause_bound = bound.clone();
                walk_sequence(
                    parts,
                    &mut clause_bound,
                    host_capabilities,
                    analysis,
                    false,
                );
            }
            _ => {
                let mut local = bound.clone();
                walk_expr(clause, &mut local, host_capabilities, analysis, false);
            }
        }
    }
}

fn walk_let(
    arguments: &[Expr],
    bound: &HashSet<String>,
    host_capabilities: &HashSet<String>,
    analysis: &mut Analysis,
    sequential: bool,
) {
    if arguments.is_empty() {
        return;
    }

    let mut body_bound = bound.clone();
    if let ExprKind::List(bindings) = &arguments[0].kind {
        for binding in bindings.iter() {
            let ExprKind::List(parts) = &binding.kind else {
                continue;
            };
            if parts.is_empty() {
                continue;
            }

            let mut initializer_bound = if sequential {
                body_bound.clone()
            } else {
                bound.clone()
            };
            for value in &parts[1..] {
                walk_expr(
                    value,
                    &mut initializer_bound,
                    host_capabilities,
                    analysis,
                    false,
                );
            }

            if let ExprKind::Symbol(name) = &parts[0].kind {
                body_bound.insert(name.to_string());
            }
        }
    }

    walk_sequence(
        &arguments[1..],
        &mut body_bound,
        host_capabilities,
        analysis,
        false,
    );
}

fn walk_expr(
    expression: &Expr,
    bound: &mut HashSet<String>,
    host_capabilities: &HashSet<String>,
    analysis: &mut Analysis,
    _top_level: bool,
) {
    let ExprKind::List(items) = &expression.kind else {
        return;
    };
    if items.is_empty() {
        return;
    }

    let head = &items[0];
    let arguments = &items[1..];
    let resolved = resolve_head(head, bound, host_capabilities, analysis);

    if let Some((surface, sens)) = resolved {
        if surface.is_some() {
            analysis.named_calls += 1;
        }

        let kind = head_kind(sens);
        if surface.is_some() {
            push_head_edit(head, sens, analysis);
        }

        match kind {
            HeadKind::Quote => return,
            HeadKind::Lambda => {
                if arguments.is_empty() {
                    return;
                }
                let mut local = bound.clone();
                collect_parameter_names(&arguments[0], &mut local);
                walk_sequence(
                    &arguments[1..],
                    &mut local,
                    host_capabilities,
                    analysis,
                    false,
                );
                return;
            }
            HeadKind::Define => {
                if arguments.is_empty() {
                    return;
                }
                if let ExprKind::Symbol(name) = &arguments[0].kind {
                    // Generic source migration must preserve lexical/surface
                    // shadowing. #1468 pins exact code slots to the first
                    // language definition, so a later top-level surface
                    // redefinition must NOT be rewritten to that old slot.
                    bound.insert(name.to_string());
                }
                walk_sequence(
                    &arguments[1..],
                    bound,
                    host_capabilities,
                    analysis,
                    false,
                );
                return;
            }
            HeadKind::Defmacro => {
                if arguments.len() < 2 {
                    return;
                }
                if let ExprKind::Symbol(name) = &arguments[0].kind {
                    // A macro definition changes subsequent surface resolution just
                    // like DEFINE. Exact code slots remain pinned independently;
                    // generic migration must preserve the new lexical macro binding.
                    bound.insert(name.to_string());
                }
                let mut local = bound.clone();
                collect_parameter_names(&arguments[1], &mut local);
                walk_sequence(
                    &arguments[2..],
                    &mut local,
                    host_capabilities,
                    analysis,
                    false,
                );
                return;
            }
            HeadKind::Let => {
                walk_let(
                    arguments,
                    bound,
                    host_capabilities,
                    analysis,
                    false,
                );
                return;
            }
            HeadKind::LetStar => {
                walk_let(
                    arguments,
                    bound,
                    host_capabilities,
                    analysis,
                    true,
                );
                return;
            }
            HeadKind::Cond => {
                walk_cond_clauses(arguments, bound, host_capabilities, analysis);
                return;
            }
            HeadKind::Other => {}
        }
    } else {
        let mut head_bound = bound.clone();
        walk_expr(
            head,
            &mut head_bound,
            host_capabilities,
            analysis,
            false,
        );
    }

    for argument in arguments {
        let mut local = bound.clone();
        walk_expr(
            argument,
            &mut local,
            host_capabilities,
            analysis,
            false,
        );
    }
}

fn analyze(
    source: &str,
    host_capabilities: &HashSet<String>,
) -> Result<Analysis, String> {
    let expressions = parse(source).map_err(|error| error.render(source))?;
    let mut analysis = Analysis::default();
    let mut bound = HashSet::new();
    walk_sequence(
        &expressions,
        &mut bound,
        host_capabilities,
        &mut analysis,
        true,
    );
    analysis.edits.sort_by_key(|edit| edit.start);

    for pair in analysis.edits.windows(2) {
        if pair[0].end > pair[1].start {
            return Err("internal error: overlapping source edits".to_string());
        }
    }

    Ok(analysis)
}

fn apply_edits(source: &str, edits: &[Edit]) -> Result<String, String> {
    let mut output = source.to_string();
    for edit in edits.iter().rev() {
        let Some(current) = output.get(edit.start..edit.end) else {
            return Err("internal error: parser span is not a UTF-8 boundary".to_string());
        };
        if current.is_empty() {
            return Err("internal error: empty call-head span".to_string());
        }
        output.replace_range(edit.start..edit.end, &edit.replacement);
    }
    Ok(output)
}

fn usage() {
    eprintln!("Usage: sens-to-sens [--check] <file>...");
}

fn main() {
    let mut check = false;
    let mut files = Vec::new();

    for argument in env::args().skip(1) {
        if argument == "--check" {
            check = true;
        } else if argument == "-h" || argument == "--help" {
            println!("Usage: sens-to-sens [--check] <file>...");
            println!("Parser-aware repository migration from admitted surfaces to exact SENS functions.");
            println!("--check reports candidates without writing and exits 1 when changes are available.");
            return;
        } else if argument.starts_with('-') {
            eprintln!("sens-to-sens: unknown option: {argument}");
            usage();
            process::exit(2);
        } else {
            files.push(argument);
        }
    }

    if files.is_empty() {
        usage();
        process::exit(2);
    }

    let host_capabilities = host_capability_names();
    let mut failed = false;
    let mut changes_available = false;

    for filename in files {
        let source = match fs::read_to_string(&filename) {
            Ok(source) => source,
            Err(error) => {
                eprintln!("sens-to-sens: {filename}: {error}");
                failed = true;
                continue;
            }
        };

        let analysis = match analyze(&source, &host_capabilities) {
            Ok(analysis) => analysis,
            Err(error) => {
                eprintln!("sens-to-sens: {filename}: {error}");
                failed = true;
                continue;
            }
        };

        if check {
            println!(
                "{filename}: convertible={} named-calls={} blocked-host={}",
                analysis.edits.len(),
                analysis.named_calls,
                analysis.blocked_host_capabilities
            );
            changes_available |= !analysis.edits.is_empty();
            continue;
        }

        let output = match apply_edits(&source, &analysis.edits) {
            Ok(output) => output,
            Err(error) => {
                eprintln!("sens-to-sens: {filename}: {error}");
                failed = true;
                continue;
            }
        };

        if let Err(error) = analyze(&output, &host_capabilities) {
            eprintln!("sens-to-sens: {filename}: rewritten source does not parse: {error}");
            failed = true;
            continue;
        }

        if output != source {
            if let Err(error) = fs::write(&filename, &output) {
                eprintln!("sens-to-sens: {filename}: {error}");
                failed = true;
                continue;
            }
        }

        let remaining =
            analyze(&output, &host_capabilities).expect("rewritten source was just validated");
        println!(
            "{filename}: replaced={} named-calls-remaining={} blocked-host={}",
            analysis.edits.len(),
            remaining.named_calls,
            remaining.blocked_host_capabilities
        );
    }

    if failed {
        process::exit(2);
    }
    if check && changes_available {
        process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn no_host() -> HashSet<String> {
        HashSet::new()
    }

    fn rewrite(source: &str) -> String {
        let hosts = no_host();
        let analysis = analyze(source, &hosts).expect("source parses");
        apply_edits(source, &analysis.edits).expect("edits apply")
    }

    #[test]
    fn preserves_comments_strings_and_quote_data() {
        let source = "; (+ 8 9)\n(quote (+ 1 2))\n\"car (+ 3 4)\"\n(atom? x)\n";
        let expected =
            "; (+ 8 9)\n(00000001 (+ 1 2))\n\"car (+ 3 4)\"\n(00000010 x)\n";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn derived_functions_and_current_macros_use_exact_codes() {
        let source =
            "(let ((xs (list 1 2 3))) (and (member? 2 xs) (or () (length xs))))";
        let expected =
            "(10011100 ((xs (00100111 1 2 3))) (10011010 (00101100 2 xs) (10011011 () (00101000 xs))))";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn defmacro_head_and_body_use_exact_sens_after_1460() {
        let source = "(defmacro twice (x) (list (quote list) x x))";
        let expected = "(00001010 twice (x) (00100111 (00000001 list) x x))";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn defmacro_target_shadows_registry_surface_for_later_calls() {
        let source = "(defmacro list args (car args)) (list (quote shadowed))";
        let expected = "(00001010 list args (00000101 args)) (list (00000001 shadowed))";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn local_bindings_shadow_registry_surfaces() {
        let source =
            "(lambda (list) (list 1 2)) (let ((car (lambda (x) x))) (car (list 1 2)))";
        let expected =
            "(00001000 (list) (list 1 2)) (10011100 ((car (00001000 (x) x))) (car (00100111 1 2)))";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn top_level_and_local_definitions_shadow_registry_surfaces() {
        let source =
            "(define list (lambda args (quote shadowed))) (list 1 2) (lambda () (define list (lambda args 7)) (list 1 2))";
        let expected =
            "(00001001 list (00001000 args (00000001 shadowed))) (list 1 2) (00001000 () (00001001 list (00001000 args 7)) (list 1 2))";
        assert_eq!(rewrite(source), expected);
    }

    #[test]
    fn compatibility_def_maps_to_define_code() {
        assert_eq!(
            rewrite("(def f (lambda (x) (car x)))"),
            "(00001001 f (00001000 (x) (00000101 x)))"
        );
    }

    #[test]
    fn direct_sens_quote_protects_quoted_data() {
        assert_eq!(
            rewrite("(00000001 (car (list 1 2)))"),
            "(00000001 (car (list 1 2)))"
        );
    }

    #[test]
    fn host_capability_collision_is_never_rewritten() {
        let source = "(car x)";
        let mut hosts = HashSet::new();
        hosts.insert("car".to_string());
        let analysis = analyze(source, &hosts).expect("source parses");
        assert!(analysis.edits.is_empty());
        assert_eq!(analysis.blocked_host_capabilities, 1);
    }

    #[test]
    fn public_sens_display_is_the_replacement_format() {
        assert_eq!(target_sens(sens::sens!(00000101)).to_string(), "00000101");
        assert_eq!(target_sens(sens::sens!(00001011)).to_string(), "00001001");
    }
}

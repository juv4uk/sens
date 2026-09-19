//! Integration witness for Issue #746 [P0][LANGUAGE-SIMPLIFY-1].
//!
//! Acceptance criterion 5:
//! "Demonstrate one program that mixes local Lisp evaluation with at least two island calls."
//!
//! Acceptance criterion 6:
//! "No semantic authority moves into Rust or a kernel as a side effect of simplification."
//!
//! This witness demonstrates that my-lisp acts as a small, honest semantic/coordination
//! language. Local Lisp evaluation handles data structure composition, while heavy
//! reasoning or relational queries are delegated to autonomous islands via opaque byte
//! transport. The native results remain intact and are composed in pure Lisp data.

use std::collections::HashMap;
use wsm_kernel_host::{KernelDriver, KernelHostError, KernelId, KernelRouter};

// ============================================================================
// 1. Autonomous Reasoning Islands (Opaque Byte Execution)
// ============================================================================

struct MockDatalogIsland {
    id: KernelId,
    running: bool,
}

impl MockDatalogIsland {
    fn new() -> Self {
        Self {
            id: KernelId::new("datalog"),
            running: false,
        }
    }
}

impl KernelDriver for MockDatalogIsland {
    fn id(&self) -> KernelId {
        self.id.clone()
    }

    fn start(&mut self) -> Result<(), KernelHostError> {
        self.running = true;
        Ok(())
    }

    fn exchange(&mut self, payload: &[u8]) -> Result<Vec<u8>, KernelHostError> {
        if !self.running {
            return Err(KernelHostError::NotRunning);
        }
        let query = String::from_utf8_lossy(payload);
        // Simulate Datalog relational closure: base facts + derived fixpoint
        let output = format!(
            "datalog-closure:ancestors_of({query})=[parent(alice,bob),parent(bob,carol),ancestor(alice,carol)]"
        );
        Ok(output.into_bytes())
    }

    fn snapshot(&self) -> Result<Vec<u8>, KernelHostError> {
        Ok(b"datalog:stratified_relational_snapshot".to_vec())
    }

    fn stop(&mut self) -> Result<(), KernelHostError> {
        self.running = false;
        Ok(())
    }
}

struct MockPrologIsland {
    id: KernelId,
    running: bool,
}

impl MockPrologIsland {
    fn new() -> Self {
        Self {
            id: KernelId::new("prolog"),
            running: false,
        }
    }
}

impl KernelDriver for MockPrologIsland {
    fn id(&self) -> KernelId {
        self.id.clone()
    }

    fn start(&mut self) -> Result<(), KernelHostError> {
        self.running = true;
        Ok(())
    }

    fn exchange(&mut self, payload: &[u8]) -> Result<Vec<u8>, KernelHostError> {
        if !self.running {
            return Err(KernelHostError::NotRunning);
        }
        let query = String::from_utf8_lossy(payload);
        // Simulate Prolog SLD resolution: backtrackable substitution answers
        let output = format!("prolog-answers:unify({query})=[Subst(X=carol),Subst(X=dave)]");
        Ok(output.into_bytes())
    }

    fn snapshot(&self) -> Result<Vec<u8>, KernelHostError> {
        Ok(b"prolog:choice_point_stack_snapshot".to_vec())
    }

    fn stop(&mut self) -> Result<(), KernelHostError> {
        self.running = false;
        Ok(())
    }
}

// ============================================================================
// 2. Pure McCarthy-7 Core Lisp Evaluator (Zero External Dependencies)
// ============================================================================

#[derive(Clone, Debug, PartialEq, Eq)]
enum Value {
    Nil,
    String(String),
    Symbol(String),
    Pair(Box<Value>, Box<Value>),
    Closure {
        params: Vec<String>,
        body: Box<Value>,
        env: HashMap<String, Value>,
    },
}

fn tokenize(src: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut chars = src.chars().peekable();
    while let Some(&c) = chars.peek() {
        match c {
            ' ' | '\t' | '\r' | '\n' => {
                chars.next();
            }
            '(' | ')' => {
                tokens.push(c.to_string());
                chars.next();
            }
            '"' => {
                chars.next();
                let mut s = String::new();
                for ch in chars.by_ref() {
                    if ch == '"' {
                        break;
                    }
                    s.push(ch);
                }
                tokens.push(format!("\"{}\"", s));
            }
            _ => {
                let mut ident = String::new();
                while let Some(&ch) = chars.peek() {
                    if ch.is_whitespace() || ch == '(' || ch == ')' || ch == '"' {
                        break;
                    }
                    ident.push(ch);
                    chars.next();
                }
                tokens.push(ident);
            }
        }
    }
    tokens
}

fn parse_tokens(tokens: &[String], pos: &mut usize) -> Result<Value, String> {
    if *pos >= tokens.len() {
        return Err("unexpected EOF".into());
    }
    let tok = &tokens[*pos];
    *pos += 1;
    if tok == "(" {
        let mut elements = Vec::new();
        while *pos < tokens.len() && tokens[*pos] != ")" {
            elements.push(parse_tokens(tokens, pos)?);
        }
        if *pos >= tokens.len() {
            return Err("unclosed paren".into());
        }
        *pos += 1; // consume ')'
        let mut list = Value::Nil;
        for el in elements.into_iter().rev() {
            list = Value::Pair(Box::new(el), Box::new(list));
        }
        Ok(list)
    } else if tok.starts_with('"') && tok.ends_with('"') && tok.len() >= 2 {
        Ok(Value::String(tok[1..tok.len() - 1].to_string()))
    } else {
        Ok(Value::Symbol(tok.clone()))
    }
}

fn parse_all(src: &str) -> Result<Vec<Value>, String> {
    let tokens = tokenize(src);
    let mut pos = 0;
    let mut exprs = Vec::new();
    while pos < tokens.len() {
        exprs.push(parse_tokens(&tokens, &mut pos)?);
    }
    Ok(exprs)
}

fn list_to_vec(mut val: &Value) -> Result<Vec<Value>, String> {
    let mut res = Vec::new();
    while let Value::Pair(head, tail) = val {
        res.push((**head).clone());
        val = tail;
    }
    if *val != Value::Nil {
        return Err("improper list in syntax".into());
    }
    Ok(res)
}

fn eval(
    val: &Value,
    env: &mut HashMap<String, Value>,
    router: &mut KernelRouter,
) -> Result<Value, String> {
    match val {
        Value::Nil | Value::String(_) | Value::Closure { .. } => Ok(val.clone()),
        Value::Symbol(s) => env
            .get(s)
            .cloned()
            .ok_or_else(|| format!("unbound symbol: {s}")),
        Value::Pair(car, cdr) => {
            if let Value::Symbol(ref op) = **car {
                if op == "define" {
                    let args = list_to_vec(cdr)?;
                    if args.len() != 2 {
                        return Err("define requires 2 args".into());
                    }
                    let name = match &args[0] {
                        Value::Symbol(s) => s.clone(),
                        _ => return Err("define name must be a symbol".into()),
                    };
                    let evaluated = eval(&args[1], env, router)?;
                    env.insert(name, evaluated);
                    return Ok(Value::Nil);
                } else if op == "lambda" {
                    let args = list_to_vec(cdr)?;
                    if args.len() != 2 {
                        return Err("lambda requires 2 args".into());
                    }
                    let params = list_to_vec(&args[0])?
                        .into_iter()
                        .map(|v| match v {
                            Value::Symbol(s) => Ok(s),
                            _ => Err("lambda param must be symbol".to_string()),
                        })
                        .collect::<Result<Vec<_>, _>>()?;
                    return Ok(Value::Closure {
                        params,
                        body: Box::new(args[1].clone()),
                        env: env.clone(),
                    });
                } else if op == "cons" {
                    let args = list_to_vec(cdr)?;
                    if args.len() != 2 {
                        return Err("cons requires 2 args".into());
                    }
                    let a = eval(&args[0], env, router)?;
                    let b = eval(&args[1], env, router)?;
                    return Ok(Value::Pair(Box::new(a), Box::new(b)));
                } else if op == "car" {
                    let args = list_to_vec(cdr)?;
                    let p = eval(&args[0], env, router)?;
                    match p {
                        Value::Pair(a, _) => return Ok(*a),
                        _ => return Err("car requires pair".into()),
                    }
                } else if op == "cdr" {
                    let args = list_to_vec(cdr)?;
                    let p = eval(&args[0], env, router)?;
                    match p {
                        Value::Pair(_, d) => return Ok(*d),
                        _ => return Err("cdr requires pair".into()),
                    }
                } else if op == "island-exchange" {
                    let args = list_to_vec(cdr)?;
                    if args.len() != 2 {
                        return Err("island-exchange requires 2 args".into());
                    }
                    let target = eval(&args[0], env, router)?;
                    let payload = eval(&args[1], env, router)?;
                    let target_str = match target {
                        Value::String(s) | Value::Symbol(s) => s,
                        _ => return Err("target must be string or symbol".into()),
                    };
                    let payload_bytes = match payload {
                        Value::String(s) => s.into_bytes(),
                        _ => return Err("payload must be string".into()),
                    };
                    let resp = router
                        .exchange(&target_str, &payload_bytes, b"my-lisp-orchestrator")
                        .map_err(|e| format!("exchange error: {e}"))?;
                    return Ok(Value::String(String::from_utf8_lossy(&resp).to_string()));
                }
            }

            let operator = eval(car, env, router)?;
            let raw_args = list_to_vec(cdr)?;
            let mut eval_args = Vec::new();
            for a in raw_args {
                eval_args.push(eval(&a, env, router)?);
            }

            match operator {
                Value::Closure {
                    params,
                    body,
                    mut env,
                } => {
                    if params.len() != eval_args.len() {
                        return Err(format!(
                            "arity mismatch: expected {}, got {}",
                            params.len(),
                            eval_args.len()
                        ));
                    }
                    for (p, arg) in params.into_iter().zip(eval_args) {
                        env.insert(p, arg);
                    }
                    eval(&body, &mut env, router)
                }
                _ => Err("cannot call non-function".into()),
            }
        }
    }
}

// ============================================================================
// 3. Integration Witness Test
// ============================================================================

#[test]
fn program_mixes_local_lisp_evaluation_with_two_autonomous_island_calls() {
    // 1. Setup multi-kernel router with Datalog and Prolog autonomous islands
    let mut router = KernelRouter::new();
    router.register(Box::new(MockDatalogIsland::new()));
    router.register(Box::new(MockPrologIsland::new()));

    // 2. Define the orchestrating program in pure my-lisp:
    // It uses:
    // - Canon 0 ()
    // - Local McCarthy-7 operations (define, cons, car, cdr)
    // - Two island calls: Datalog (relational closure) and Prolog (unification search)
    // - Composes an honest Lisp observation data structure without domain collapse.
    let program = r#"
        (define pair (lambda (a b) (cons a b)))

        (define orchestrate-inquiry
          (lambda (entity)
            ((lambda (req)
               ((lambda (datalog-facts)
                  ((lambda (prolog-proof)
                     (pair (pair "request" req)
                           (pair (pair "datalog-evidence" datalog-facts)
                                 (pair (pair "prolog-evidence" prolog-proof)
                                       ()))))
                   (island-exchange "prolog" entity)))
                (island-exchange "datalog" entity)))
             (pair "query-target" entity))))

        (orchestrate-inquiry "person(alice)")
    "#;

    let mut env = HashMap::new();
    let exprs = parse_all(program).expect("program must parse");

    let mut final_value = Value::Nil;
    for expr in &exprs {
        final_value = eval(expr, &mut env, &mut router).expect("evaluation must succeed");
    }

    // 3. Verify the resulting Lisp data structure:
    // Expected structure:
    // (("request" . ("query-target" . "person(alice)"))
    //  ("datalog-evidence" . "datalog-closure:ancestors_of(person(alice))=[parent(alice,bob),parent(bob,carol),ancestor(alice,carol)]")
    //  ("prolog-evidence" . "prolog-answers:unify(person(alice))=[Subst(X=carol),Subst(X=dave)]"))
    match &final_value {
        Value::Pair(entry1, rest1) => {
            // First entry: ("request" . ("query-target" . "person(alice)"))
            match &**entry1 {
                Value::Pair(k, v) => {
                    assert_eq!(**k, Value::String("request".into()));
                    match &**v {
                        Value::Pair(rk, rv) => {
                            assert_eq!(**rk, Value::String("query-target".into()));
                            assert_eq!(**rv, Value::String("person(alice)".into()));
                        }
                        _ => panic!("expected nested request pair"),
                    }
                }
                _ => panic!("expected pair for entry1"),
            }

            // Second entry: ("datalog-evidence" . ...)
            match &**rest1 {
                Value::Pair(entry2, rest2) => {
                    match &**entry2 {
                        Value::Pair(k, v) => {
                            assert_eq!(**k, Value::String("datalog-evidence".into()));
                            assert!(match &**v {
                                Value::String(ref s) =>
                                    s.contains("datalog-closure:ancestors_of(person(alice))"),
                                _ => false,
                            });
                        }
                        _ => panic!("expected pair for entry2"),
                    }

                    // Third entry: ("prolog-evidence" . ...)
                    match &**rest2 {
                        Value::Pair(entry3, rest3) => {
                            match &**entry3 {
                                Value::Pair(k, v) => {
                                    assert_eq!(**k, Value::String("prolog-evidence".into()));
                                    assert!(match &**v {
                                        Value::String(ref s) =>
                                            s.contains("prolog-answers:unify(person(alice))"),
                                        _ => false,
                                    });
                                }
                                _ => panic!("expected pair for entry3"),
                            }
                            // Terminates with Canon 0 ()
                            assert_eq!(**rest3, Value::Nil);
                        }
                        _ => panic!("expected pair for rest2"),
                    }
                }
                _ => panic!("expected pair for rest1"),
            }
        }
        other => panic!("expected nested Lisp pairs, got {:?}", other),
    }
}

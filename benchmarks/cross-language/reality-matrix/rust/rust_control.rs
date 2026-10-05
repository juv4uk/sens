use std::{env, hint::black_box, process, time::Instant};

#[derive(Debug)]
enum Value {
    Nil,
    Pair(Box<Value>, Box<Value>),
}

fn setup(case: &str) -> Result<Value, String> {
    match case {
        "d3-quote-empty" => Ok(Value::Nil),
        "d3-car-empty" => Ok(Value::Pair(Box::new(Value::Nil), Box::new(Value::Nil))),
        other => Err(format!("unknown case: {other}")),
    }
}

fn step<'a>(case: &str, value: &'a Value) -> Result<&'a Value, String> {
    match case {
        "d3-quote-empty" => Ok(value),
        "d3-car-empty" => match value {
            Value::Pair(head, _tail) => Ok(head),
            Value::Nil => Err("CAR received Nil".to_owned()),
        },
        other => Err(format!("unknown case: {other}")),
    }
}

fn fingerprint(value: &Value) -> &'static str {
    match value {
        Value::Nil => "()",
        Value::Pair(_, _) => "pair",
    }
}

fn run() -> Result<(), String> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 3 || args.len() > 4 {
        return Err(format!(
            "usage: {} <d3-quote-empty|d3-car-empty> <preflight|repeated> [repeat]",
            args.first().map(String::as_str).unwrap_or("rust_control")
        ));
    }

    let case = black_box(args[1].as_str());
    let mode = args[2].as_str();
    let repeat = if args.len() == 4 {
        args[3]
            .parse::<usize>()
            .map_err(|e| format!("invalid repeat count: {e}"))?
    } else {
        1
    };

    let state = black_box(setup(case)?);

    match mode {
        "preflight" => {
            let result = step(case, black_box(&state))?;
            println!("VALUE={}", fingerprint(result));
            println!("ELAPSED_NS=0");
        }
        "repeated" => {
            if repeat == 0 {
                return Err("repeat must be greater than zero".to_owned());
            }
            let started = Instant::now();
            let mut last = None;
            for _ in 0..repeat {
                let result = step(case, black_box(&state))?;
                black_box(result);
                last = Some(result);
            }
            let elapsed = started.elapsed().as_nanos();
            let result = last.expect("repeat > 0");
            println!("VALUE={}", fingerprint(result));
            println!("ELAPSED_NS={elapsed}");
        }
        other => return Err(format!("unknown mode: {other}")),
    }
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("ERROR: {error}");
        process::exit(2);
    }
}

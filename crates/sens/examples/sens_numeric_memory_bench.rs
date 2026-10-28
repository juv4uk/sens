//! Вузький вимір RSS для копій D24+ чисел усередині SENS evaluator.
//!
//! Відтворює чинний точний D2/D3 шлях із уже сформованих слів. D3 `як-є`
//! повертає те саме D24+ значення повторно; результати утримуються, щоб
//! whole-process RSS показав вартість спільного сховища проти deep-copy
//! контрольного режиму. T5M-декодування й CPU-таймінг тут не вимірюються.

use sens::{BinaryNumber, DomainIdentity, ExactDomainWord, PhysicalT5Program, Session, Value};
use std::{env, hint::black_box, process};

const MAX_WIDTH_BITS: usize = 196_608;
const MAX_RETAINED_VALUES: usize = 512;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Strategy {
    Shared,
    DeepCopy,
}

impl Strategy {
    fn from_arg(value: &str) -> Result<Self, String> {
        match value {
            "shared" => Ok(Self::Shared),
            "deep-copy" => Ok(Self::DeepCopy),
            _ => Err("mode must be shared or deep-copy".into()),
        }
    }

    fn label(self) -> &'static str {
        match self {
            Self::Shared => "shared",
            Self::DeepCopy => "deep-copy",
        }
    }
}

fn identity(width: u8, bits: u16) -> ExactDomainWord {
    let coordinate = sens::domain_ladder::DomainCoordinate::new(width, bits)
        .expect("benchmark uses exact in-range domain coordinates");
    ExactDomainWord::identity(DomainIdentity::from_coordinate(coordinate))
}

fn program(width_bits: usize) -> Result<PhysicalT5Program, String> {
    if !BinaryNumber::is_numeric_domain_width(width_bits) || width_bits > MAX_WIDTH_BITS {
        return Err(format!(
            "width must be a current D24+ width no greater than {MAX_WIDTH_BITS} bits"
        ));
    }

    // All ones is a full-width negative D24+ word under the current
    // two's-complement numeric law. Keeping every bit significant makes the
    // deep-copy control's storage cost observable rather than benchmarking
    // a normalized one-bit magnitude.
    let value = BinaryNumber::from_numeric_domain_bits(width_bits, &vec![1; width_bits])
        .ok_or_else(|| "could not construct the exact D24+ benchmark word".to_string())?;
    let words = vec![
        identity(2, 0b10),  // D2 open
        identity(3, 0b001), // D3 QUOTE / `як-є`
        identity(2, 0b00),  // D2 separator
        ExactDomainWord::number(value).map_err(str::to_owned)?,
        identity(2, 0b01), // D2 close
    ];
    PhysicalT5Program::from_exact_domain_words_owned(words)
        .map_err(|error| format!("exact SENS quote program was rejected: {error}"))
}

fn execute_and_retain(
    strategy: Strategy,
    width_bits: usize,
    retained_values: usize,
) -> Result<Vec<Value>, String> {
    if retained_values == 0 || retained_values > MAX_RETAINED_VALUES {
        return Err(format!(
            "retained values must be between 1 and {MAX_RETAINED_VALUES}"
        ));
    }

    let program = program(width_bits)?;
    let mut session = Session::bare();
    let mut retained = Vec::with_capacity(retained_values);
    for _ in 0..retained_values {
        let result = program
            .execute(&mut session)
            .map_err(|error| format!("SENS evaluator failed: {error}"))?;
        let Value::BinaryNumber(number) = &result.value else {
            return Err("D3 `як-є` did not return the exact D24+ number".into());
        };
        if number.numeric_domain_width() != Some(width_bits) || number.width() != width_bits {
            return Err("SENS evaluator changed the exact D24+ width or bits".into());
        }

        let value = match strategy {
            Strategy::Shared => number.clone(),
            Strategy::DeepCopy => {
                let exact_bits = number
                    .exact_numeric_domain_bits()
                    .ok_or_else(|| "SENS result lost its D24+ identity".to_string())?;
                let copy = BinaryNumber::from_numeric_domain_bits(width_bits, &exact_bits)
                    .ok_or_else(|| "deep-copy control could not retain exact D24+".to_string())?;
                if &copy != number {
                    return Err("deep-copy control changed the SENS result".into());
                }
                copy
            }
        };
        retained.push(Value::BinaryNumber(value));
    }

    if retained.len() != retained_values {
        return Err("not all SENS evaluator results were retained".into());
    }
    black_box(&retained);
    Ok(retained)
}

fn run() -> Result<(), String> {
    let args: Vec<_> = env::args().collect();
    if args.len() != 4 {
        return Err(
            "usage: sens_numeric_memory_bench <shared|deep-copy> WIDTH_BITS RETAINED_VALUES".into(),
        );
    }
    // Diagnostic only: actual host layout is not a SENS domain law.
    // Keep stdout's benchmark record stable; RSS and allocator costs
    // still require whole-process measurements on the same runner.
    eprintln!(
        "SENS_HOST_LAYOUT value_bytes={} rational_bytes={} binary_number_bytes={} environment_bytes={} pair_node_bytes={} pair_handle_bytes={} pair_allocations_per_cons=1",
        std::mem::size_of::<Value>(),
        std::mem::size_of::<sens::Rational>(),
        std::mem::size_of::<BinaryNumber>(),
        std::mem::size_of::<sens::Environment>(),
        std::mem::size_of::<sens::PairNode>(),
        std::mem::size_of::<std::rc::Rc<sens::PairNode>>(),
    );
    let strategy = Strategy::from_arg(&args[1])?;
    let width_bits = args[2]
        .parse::<usize>()
        .map_err(|_| "WIDTH_BITS must be a decimal integer".to_string())?;
    let retained_values = args[3]
        .parse::<usize>()
        .map_err(|_| "RETAINED_VALUES must be a decimal integer".to_string())?;
    let values = execute_and_retain(strategy, width_bits, retained_values)?;
    black_box(values);
    println!(
        "SENS_NUMERIC_MEMORY\tmode={}\twidth_bits={}\tretained={}\tverified={}",
        strategy.label(),
        width_bits,
        retained_values,
        retained_values
    );
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("SENS_NUMERIC_MEMORY_FAIL: {error}");
        process::exit(1);
    }
}


use sens::inventory_binary_contract;
use serde_json::{Map, Value};
use std::env;
use std::fs;
use std::process::ExitCode;

fn render_inventory(source: &str) -> Result<Value, String> {
    let inventory = inventory_binary_contract(source).map_err(|error| error.to_string())?;

    let mut residents = Map::new();
    for (width, values) in inventory.residents() {
        residents.insert(
            format!("D{width}"),
            Value::Array(
                values
                    .iter()
                    .map(|value| Value::String(format!("{value:0width$b}")))
                    .collect(),
            ),
        );
    }

    let d2_structure = inventory
        .d2_structure()
        .iter()
        .map(|value| Value::String(format!("{value:02b}")))
        .collect::<Vec<_>>();

    Ok(serde_json::json!({
        "schema": "sens-binary-contract-inventory/v1",
        "reader": "canonical-visible-binary",
        "d2_structure": d2_structure,
        "d2_complete": inventory.has_complete_d2_structure(),
        "residents": residents,
        "coordinate_count": inventory.ordered_coordinates().len()
    }))
}

fn main() -> ExitCode {
    let mut args = env::args_os();
    let program = args.next().unwrap_or_default();
    let Some(path) = args.next() else {
        eprintln!("usage: {} <canonical-binary-contract.lisp>", program.to_string_lossy());
        return ExitCode::from(2);
    };
    if args.next().is_some() {
        eprintln!("usage: {} <canonical-binary-contract.lisp>", program.to_string_lossy());
        return ExitCode::from(2);
    }

    let source = match fs::read_to_string(&path) {
        Ok(source) => source,
        Err(error) => {
            eprintln!("{}: {error}", path.to_string_lossy());
            return ExitCode::from(2);
        }
    };

    match render_inventory(&source) {
        Ok(value) => {
            println!(
                "{}",
                serde_json::to_string_pretty(&value).expect("JSON inventory serialization")
            );
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("binary contract rejected: {error}");
            ExitCode::from(1)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn json_projection_preserves_exact_widths() {
        let value = render_inventory(
            "10 1 00 001 11 000000001 01 00 0001 00 00000001",
        )
        .expect("canonical binary inventory");

        assert_eq!(value["d2_complete"], true);
        assert_eq!(value["residents"]["D1"][0], "1");
        assert_eq!(value["residents"]["D3"][0], "001");
        assert_eq!(value["residents"]["D4"][0], "0001");
        assert_eq!(value["residents"]["D8"][0], "00000001");
        assert_eq!(value["residents"]["D9"][0], "000000001");
    }

    #[test]
    fn malformed_source_never_gets_an_inventory() {
        assert!(render_inventory("10 001").is_err());
    }
}

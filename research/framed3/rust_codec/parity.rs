#[path = "senc.rs"]
mod senc;

use senc::{decode_senc, encode_smallest, read_carrier, Carrier, Profile, SencError};
use std::io::{self, BufRead};

fn unhex(text: &str) -> Result<Vec<u8>, String> {
    if text.len() % 2 != 0 || !text.is_ascii() {
        return Err(format!("invalid hex width or UTF-8: {text}"));
    }
    (0..text.len()).step_by(2).map(|i| {
        u8::from_str_radix(&text[i..i + 2], 16)
            .map_err(|_| format!("invalid hex digit: {text}"))
    }).collect()
}

fn profile_from(text: &str) -> Option<Profile> {
    match text {
        "T5" => Some(Profile::T5),
        "Frame3" => Some(Profile::Frame3),
        "Tb33" => Some(Profile::Tb33),
        _ => None,
    }
}

fn extension_of(profile: Profile) -> &'static str {
    match profile {
        Profile::T5 => ".sens",
        _ => ".senc",
    }
}

fn main() {
    let stdin = io::stdin();
    let mut total = 0usize;
    let mut failures = 0usize;
    let mut physical = 0usize;
    let mut admitted = 0usize;
    let mut correctly_refused = 0usize;
    let mut choices = 0usize;
    let mut negative = 0usize;

    for raw in stdin.lock().lines() {
        let raw = raw.expect("missing input line");
        if raw.trim().is_empty() {
            continue;
        }
        total += 1;
        let fields: Vec<&str> = raw.split('\t').collect();

        if fields[0] == "NEG" {
            if fields.len() != 3 {
                eprintln!("[NEG] malformed negative record: {raw}");
                failures += 1;
                continue;
            }
            let kind = fields[1];
            let Ok(data) = unhex(fields[2]) else {
                failures += 1;
                continue;
            };
            let rejected = match kind {
                "T5" => read_carrier(&Carrier {
                    profile: Profile::T5,
                    data: data.clone(),
                    extension: ".sens",
                }).is_err(),
                "F3" | "F4" => decode_senc(&data).is_err(),
                _ => false,
            };
            if !rejected {
                eprintln!("[NEG] {kind} {:?} not rejected", fields[2]);
                failures += 1;
            } else {
                negative += 1;
            }
            continue;
        }

        if fields.len() != 7 || !matches!(fields[6], "D3" | "REJECT") {
            eprintln!("[PROTOCOL] expected 7 fields incl independent Python D3 verdict: {raw}");
            failures += 1;
            continue;
        }
        let d3_admitted = fields[6] == "D3";
        let words: Vec<String> = fields[0].split_whitespace().map(str::to_string).collect();

        // Python's legacy profile choice is an oracle only for the admitted
        // D3 executable subset; rejected DATA shapes are not executable code.
        if d3_admitted {
            if let Some(profile) = profile_from(fields[4]) {
                let Ok(data) = unhex(fields[5]) else {
                    failures += 1;
                    continue;
                };
                let expected = Carrier {
                    profile,
                    data,
                    extension: extension_of(profile),
                };
                match encode_smallest(&words) {
                    Ok(got) if got == expected => choices += 1,
                    other => {
                        eprintln!("[CHOOSE-admitted] {:?}\n  got  {:?}\n  want {:?}", fields[0], other, expected);
                        failures += 1;
                    }
                }
            }
        }

        let Ok(t5bytes) = unhex(fields[1]) else {
            failures += 1;
            continue;
        };
        let t5 = Carrier {
            profile: Profile::T5,
            data: t5bytes,
            extension: ".sens",
        };
        match read_carrier(&t5) {
            Ok(decoded) if decoded == words => physical += 1,
            other => {
                eprintln!("[T5 physical] {:?} -> {:?}", fields[0], other);
                failures += 1;
            }
        }

        for (index, profile, label) in [
            (2, Profile::Frame3, "F3"),
            (3, Profile::Tb33, "F4"),
        ] {
            if fields[index] == "-" {
                continue;
            }
            let Ok(body) = unhex(fields[index]) else {
                failures += 1;
                continue;
            };
            let mut data = vec![if index == 2 { 0xF3 } else { 0xF4 }];
            data.extend_from_slice(&body);
            let carrier = Carrier {
                profile,
                data: data.clone(),
                extension: ".senc",
            };

            // The cross-language *physical* oracle checks ALL valid
            // Python-encoded structural data, not only executable D3 code.
            match read_carrier(&carrier) {
                Ok(decoded) if decoded == words => physical += 1,
                other => {
                    eprintln!("[{label}-physical] {:?} -> {:?}", fields[0], other);
                    failures += 1;
                    continue;
                }
            }
            match decode_senc(&data) {
                Ok(decoded) if d3_admitted && decoded == words => admitted += 1,
                Err(SencError::NotCanonical) if !d3_admitted => correctly_refused += 1,
                other => {
                    eprintln!(
                        "[{label}-D3] {:?} Python={} Rust={:?}",
                        fields[0], fields[6], other
                    );
                    failures += 1;
                }
            }
        }
    }
    eprintln!(
        "=== parity: {total} records, {physical} independently checked physical \
         roundtrips, {admitted} independently admitted D3, \
         {correctly_refused} independently rejected D3, \
         {choices} admitted codec-choice checks, {negative} negative vectors, \
         {failures} failures ==="
    );
    if physical == 0 || admitted == 0 || correctly_refused == 0
        || choices == 0 || negative == 0 || failures != 0
    {
        std::process::exit(1);
    }
}

#[path = "senc.rs"]
mod senc;

use senc::{decode_senc, encode_smallest, read_carrier, Carrier, Profile};
use std::io::{self, BufRead};

fn unhex(text: &str) -> Vec<u8> {
    let bytes = text.as_bytes();
    let mut out = Vec::with_capacity(bytes.len() / 2);
    let mut i = 0;
    while i + 1 < bytes.len() {
        let hi = (bytes[i] as char).to_digit(16).unwrap() as u8;
        let lo = (bytes[i + 1] as char).to_digit(16).unwrap() as u8;
        out.push((hi << 4) | lo);
        i += 2;
    }
    out
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
    for raw in stdin.lock().lines() {
        let raw = raw.unwrap();
        if raw.trim().is_empty() {
            continue;
        }
        total += 1;
        let fields: Vec<&str> = raw.split('\t').collect();

        if fields[0] == "NEG" {
            let kind = fields[1];
            let data = unhex(fields[2]);
            let rejected = match kind {
                "T5" => read_carrier(&Carrier {
                    profile: Profile::T5,
                    data: data.clone(),
                    extension: ".sens",
                })
                .is_err(),
                _ => decode_senc(&data).is_err(),
            };
            if !rejected {
                eprintln!("[NEG] {kind} {:?} не відкинуто", fields[2]);
                failures += 1;
            }
            continue;
        }

        let words: Vec<String> = fields[0].split_whitespace().map(|s| s.to_string()).collect();

        if let Some(profile) = profile_from(fields[4]) {
            let expected = Carrier {
                profile,
                data: unhex(fields[5]),
                extension: extension_of(profile),
            };
            match encode_smallest(&words) {
                Ok(got) if got == expected => {}
                other => {
                    eprintln!("[CHOOSE] {:?}\n  got  {:?}\n  want {:?}", fields[0], other, expected);
                    failures += 1;
                }
            }
        }

        let t5 = Carrier {
            profile: Profile::T5,
            data: unhex(fields[1]),
            extension: ".sens",
        };
        match read_carrier(&t5) {
            Ok(decoded) if decoded == words => {}
            other => {
                eprintln!("[T5] {:?} -> {:?}", fields[0], other);
                failures += 1;
            }
        }

        if fields[2] != "-" {
            let mut data = vec![0xF3u8];
            data.extend_from_slice(&unhex(fields[2]));
            let carrier = Carrier {
                profile: Profile::Frame3,
                data: data.clone(),
                extension: ".senc",
            };
            match read_carrier(&carrier) {
                Ok(decoded) if decoded == words => {}
                other => {
                    eprintln!("[F3] {:?} -> {:?}", fields[0], other);
                    failures += 1;
                }
            }
            match decode_senc(&data) {
                Ok(decoded) if decoded == words => {}
                other => {
                    eprintln!("[F3-senc] {:?} -> {:?}", fields[0], other);
                    failures += 1;
                }
            }
        }

        if fields[3] != "-" {
            let mut data = vec![0xF4u8];
            data.extend_from_slice(&unhex(fields[3]));
            let carrier = Carrier {
                profile: Profile::Tb33,
                data: data.clone(),
                extension: ".senc",
            };
            match read_carrier(&carrier) {
                Ok(decoded) if decoded == words => {}
                other => {
                    eprintln!("[F4] {:?} -> {:?}", fields[0], other);
                    failures += 1;
                }
            }
            match decode_senc(&data) {
                Ok(decoded) if decoded == words => {}
                other => {
                    eprintln!("[F4-senc] {:?} -> {:?}", fields[0], other);
                    failures += 1;
                }
            }
        }
    }
    eprintln!("=== parity: {}/{} ok, {} failures ===", total - failures, total, failures);
    if failures > 0 {
        std::process::exit(1);
    }
}

//! Matched Frame3 Carrier benchmark for Zig f3c_bench.zig.
//! Physical encode/decode only; no claim to define SENS semantics.
use sens::frame3_small::{decode_explicit_small_f3, encode_explicit_small_f3};
use std::hint::black_box;
use std::time::Instant;

fn hex(bytes: &[u8]) -> String {
    const ALPHABET: &[u8; 16] = b"0123456789abcdef";
    let mut s = String::with_capacity(bytes.len() * 2);
    for &byte in bytes {
        s.push(ALPHABET[(byte >> 4) as usize] as char);
        s.push(ALPHABET[(byte & 15) as usize] as char);
    }
    s
}

fn trial(name: &str, op: &str, t5: &[u8], f3c: &[u8], reps: usize) -> u128 {
    let start = Instant::now();
    for _ in 0..reps {
        match op {
            "encode" => {
                black_box(
                    encode_explicit_small_f3(black_box(t5))
                        .expect("Rust F3C encode")
                        .expect("Rust F3C must save physical bytes"),
                );
            }
            "decode" => {
                black_box(decode_explicit_small_f3(black_box(f3c)).expect("Rust F3C decode"));
            }
            _ => panic!("unsupported operation"),
        }
    }
    let elapsed_ns = start.elapsed().as_nanos();
    println!(
        "sample impl=rust case={name} op={op} elapsed_ns={} reps={reps}",
        elapsed_ns
    );
    elapsed_ns
}
fn main() {
    let cases: [(&str, &[u8], &[u8], usize); 2] = [
        ("quote", &[0x63, 0x89, 0x06, 0xa1], &[0xf3, 0x40, 0x60], 512),
        (
            "car_cons",
            &[0x66, 0x38, 0x67, 0x89, 0x89, 0x3b, 0x35],
            &[0xf3, 0x36, 0x5f, 0x1b, 0xd0, 0xc9],
            256,
        ),
    ];
    // Неканонічний F3C не допускається, а T5 fallback не припустимий.
    // Перевірка поза таймінгом, жодного host-оракула SENS.
    assert!(
        decode_explicit_small_f3(&[0xf4, 0x40, 0x60]).is_err(),
        "wrong F3C carrier tag must be rejected"
    );
    for (name, input, expected, reps) in cases {
        let encoded = encode_explicit_small_f3(input)
            .expect("Rust encode")
            .expect("Rust must select tiny F3C");
        assert_eq!(encoded, expected, "physical F3C byte parity");
        let recovered = decode_explicit_small_f3(expected).expect("Rust decode");
        assert_eq!(recovered, input, "physical T5 restored");
        println!("physical impl=rust case={name} hex={}", hex(&encoded));
        println!(
            "fixture impl=rust case={name} t5_bytes={} f3c_bytes={}",
            input.len(),
            encoded.len()
        );
        // Прогрів відділений від вимірювання; F3C — транспорт, не Lisp.
        for _ in 0..5 {
            black_box(encode_explicit_small_f3(black_box(input)).unwrap());
            black_box(decode_explicit_small_f3(black_box(expected)).unwrap());
        }
        let mut encode_ns = [0_u128; 11];
        let mut decode_ns = [0_u128; 11];
        // AB/BA порядок для зменшення систематичного кеш-ефекту.
        for i in 0..11 {
            if i % 2 == 0 {
                encode_ns[i] = trial(name, "encode", input, expected, reps);
                decode_ns[i] = trial(name, "decode", input, expected, reps);
            } else {
                decode_ns[i] = trial(name, "decode", input, expected, reps);
                encode_ns[i] = trial(name, "encode", input, expected, reps);
            }
        }
        for (op, mut samples) in [("encode", encode_ns), ("decode", decode_ns)] {
            samples.sort_unstable();
            println!(
                "summary impl=rust case={name} op={op} p50_ns_per_op={} p90_ns_per_op={}                  samples=11 warmup=5 reps={reps} scope=allocating_transport_only release=NOT_CERTIFIED",
                samples[5] / reps as u128,
                samples[9] / reps as u128
            );
        }
    }
}

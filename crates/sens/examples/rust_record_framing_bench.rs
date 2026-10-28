//! Бенчмарк механізму Rust: обхід записів із 4-байтовою довжиною.
//! Жодної семантики Lisp/SENS, жодного висновку про швидкість eval.
//! Самодостатній корпус, валідація помилок ДО вимірювання, 11 сирих проб.

use std::{hint::black_box, time::Instant};

fn inspect_frames(bytes: &[u8]) -> Result<(usize, usize), &'static str> {
    let mut offset = 0usize;
    let mut frames = 0usize;
    let mut payload_bytes = 0usize;
    while offset < bytes.len() {
        let header_end = offset.checked_add(4).ok_or("header overflow")?;
        let header = bytes.get(offset..header_end).ok_or("truncated header")?;
        let size = u32::from_le_bytes(header.try_into().map_err(|_| "invalid header")?) as usize;
        offset = header_end;
        let record_end = offset.checked_add(size).ok_or("record overflow")?;
        bytes.get(offset..record_end).ok_or("truncated payload")?;
        payload_bytes = payload_bytes.checked_add(size).ok_or("payload overflow")?;
        offset = record_end;
        frames += 1;
    }
    if frames == 0 {
        return Err("empty corpus");
    }
    Ok((frames, payload_bytes))
}

fn corpus() -> Vec<u8> {
    let mut out = Vec::new();
    for index in 0usize..256 {
        let size = 8 + index % 64;
        out.extend_from_slice(&(size as u32).to_le_bytes());
        out.extend((0..size).map(|n| ((n + index) % 251) as u8));
    }
    out
}

fn main() {
    const SAMPLES: usize = 11;
    const ITERATIONS: usize = 256;
    let data = corpus();
    let expected = inspect_frames(&data).expect("valid physical frame corpus");
    assert_eq!(expected.0, 256);
    // Сторонній механізм не може бути виправданий просто ненульовим виходом.
    for broken in [&data[..0], &data[..3], &data[..data.len() - 1]] {
        assert!(inspect_frames(broken).is_err(), "truncated frame accepted");
    }
    let mut elapsed_ns = [0u128; SAMPLES];
    let mut checksum: usize = 0;

    // Прогрівальний пакет виконується поза часовими пробами.
    for _ in 0..ITERATIONS {
        let result = inspect_frames(black_box(&data)).expect("corpus changed");
        assert_eq!(result, expected, "frame count/size drift during warmup");
        checksum = checksum.wrapping_add(black_box(result.1));
    }

    for sample in &mut elapsed_ns {
        let start = Instant::now();
        for _ in 0..ITERATIONS {
            let result = inspect_frames(black_box(&data)).expect("corpus changed");
            assert_eq!(result, expected, "frame count/size drift");
            checksum = checksum.wrapping_add(black_box(result.1));
        }
        *sample = start.elapsed().as_nanos();
    }
    let mut sorted = elapsed_ns;
    sorted.sort_unstable();
    assert!(sorted[0] > 0, "clock resolution insufficient");
    println!(
        "RUST_FRAME_BENCH frames={} payload_bytes={} iterations={} warmup_iterations={} samples={} p50_ns={} p90_ns={} min_ns={} max_ns={} checksum={} scope=rust-framing-only",
        expected.0, expected.1, ITERATIONS, ITERATIONS, SAMPLES,
        sorted[5], sorted[9], sorted[0], sorted[10], checksum
    );
    for (index, value) in elapsed_ns.into_iter().enumerate() {
        println!("RUST_FRAME_SAMPLE sample={} elapsed_ns={}", index + 1, value);
    }
}


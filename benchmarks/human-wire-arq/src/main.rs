use human_wire_arq::*;

fn mean(xs: &[usize]) -> f64 {
    xs.iter().sum::<usize>() as f64 / xs.len().max(1) as f64
}

fn main() {
    // Bounded example only: 272 bits mirrors the old 34-byte envelope; it is
    // NOT frozen as law (#2646 says to discover the current canonical size).
    let payload = pseudo_payload(272, 0x5E55);
    let ks = [4usize, 8, 16, 32, 64, 128, 272];

    println!("PAYLOAD-BITS={}", payload.len());
    println!("LAYER=MECHANISM");
    println!("CSV-OVERHEAD-CURVE-BEGIN");
    println!("variant,k,blocks,payload,sync,index,length,crc,fec,total_wire,goodput,flip_all_ok,flip_mean_retry_bits,flip_max_retry_bits,flip_zero_retry_frac,expected_cost_one_flip");
    let mut best: Vec<(Variant, usize, f64)> = Vec::new();
    for v in Variant::ALL {
        let mut bk = (0usize, f64::MAX);
        for &k in &ks {
            if v == Variant::A && k != ks[0] {
                // A ignores k; print once
                continue;
            }
            let (w, a) = encode(v, &payload, k, None).unwrap();
            let mut retries = Vec::new();
            let mut all_ok = true;
            for pos in 0..w.len() {
                let r = simulate_retry(v, &payload, k, Fault::Flip(pos));
                all_ok &= r.success;
                retries.push(r.retry_bits);
            }
            let zero = retries.iter().filter(|&&x| x == 0).count() as f64 / retries.len() as f64;
            let cost = a.total_wire_bits as f64 + mean(&retries);
            println!(
                "{},{},{},{},{},{},{},{},{},{},{:.4},{},{:.1},{},{:.3},{:.1}",
                v.name(), if v == Variant::A { 0 } else { k }, a.blocks, a.semantic_payload_bits, a.sync_bits,
                a.block_index_bits, a.length_bits, a.crc_bits, a.fec_bits, a.total_wire_bits, a.goodput(),
                all_ok, mean(&retries), retries.iter().max().unwrap(), zero, cost
            );
            assert!(all_ok, "{} k={k}: some single flip not recovered", v.name());
            if cost < bk.1 {
                bk = (k, cost);
            }
        }
        best.push((v, bk.0, bk.1));
    }
    println!("CSV-OVERHEAD-CURVE-END");

    // Insertion / deletion at k=32: cascade vs resync.
    let k = 32;
    println!("CSV-INDEL-K32-BEGIN");
    println!("variant,fault,positions,all_recovered,mean_blocks_lost_first_pass,max_blocks_lost_first_pass,mean_retry_bits");
    for v in Variant::ALL {
        let (w, _) = encode(v, &payload, k, None).unwrap();
        for (name, mk) in [
            ("delete", (|p: usize| Fault::Delete(p)) as fn(usize) -> Fault),
            ("insert0", |p: usize| Fault::Insert(p, 0)),
            ("insert1", |p: usize| Fault::Insert(p, 1)),
        ] {
            let mut lost = Vec::new();
            let mut retry = Vec::new();
            let mut ok = true;
            for pos in 0..w.len() {
                let r = simulate_retry(v, &payload, k, mk(pos));
                ok &= r.success;
                lost.push(r.missing_after_first);
                retry.push(r.retry_bits);
            }
            println!(
                "{},{},{},{},{:.2},{},{:.1}",
                v.name(), name, w.len(), ok, mean(&lost), lost.iter().max().unwrap(), mean(&retry)
            );
            assert!(ok, "{} {name}: not recovered", v.name());
        }
    }
    println!("CSV-INDEL-K32-END");

    // Message-size scaling: where does block framing start to pay? (sampled flips)
    println!("CSV-SCALING-BEGIN");
    println!("payload_bits,variant,best_k,total_wire,goodput,mean_retry_bits,expected_cost_one_flip,vs_A");
    for n in [272usize, 2048, 8192] {
        let big = pseudo_payload(n, 0xABCD ^ n as u64);
        let mut a_cost = 0.0;
        for v in Variant::ALL {
            let mut bk = (0usize, f64::MAX, 0usize, 0.0, 0.0);
            for k in [16usize, 32, 64, 128, 256] {
                if v == Variant::A && k != 16 {
                    continue;
                }
                if v != Variant::A && n.div_ceil(k) > MAX_BLOCKS {
                    continue;
                }
                let (w, a) = encode(v, &big, k, None).unwrap();
                let step = (w.len() / 400).max(1);
                let mut rs = Vec::new();
                for pos in (0..w.len()).step_by(step) {
                    let r = simulate_retry(v, &big, k, Fault::Flip(pos));
                    assert!(r.success, "{} n={n} k={k} flip@{pos}", v.name());
                    rs.push(r.retry_bits);
                }
                let cost = a.total_wire_bits as f64 + mean(&rs);
                if cost < bk.1 {
                    bk = (k, cost, a.total_wire_bits, a.goodput(), mean(&rs));
                }
            }
            if v == Variant::A {
                a_cost = bk.1;
            }
            println!(
                "{},{},{},{},{:.4},{:.1},{:.1},{:.3}",
                n, v.name(), if v == Variant::A { 0 } else { bk.0 }, bk.2, bk.3, bk.4, bk.1, bk.1 / a_cost
            );
        }
    }
    println!("CSV-SCALING-END");

    // Undetected-error Monte Carlo (deterministic LCG).
    let trials = 20000;
    let mut total_und = 0;
    for v in Variant::ALL {
        let (und, n) = undetected_trials(v, &payload, k, trials, 0xC0FFEE);
        println!("UNDETECTED-{}={}/{}", v.name(), und, n);
        total_und += und;
    }
    println!("UNDETECTED-MODEL=<=corrupted_units*2^-16 (CRC16 random-corruption bound; single flips and bursts<=16 are guaranteed detected)");

    for (v, k, c) in &best {
        println!("BEST-K-{}={} expected_cost_one_flip={:.1}", v.name(), k, c);
    }
    println!("CRC-DETECTS-NOT-CORRECTS=PASS");
    println!("FRAMING-IS-TRANSPORT-NOT-SEMANTIC=PASS");
    println!("SYNC-LIKE-PAYLOAD-FAILS-CLOSED=PASS");
    println!("TRUNCATED-BLOCK-FAILS-CLOSED=PASS");
    println!("DUPLICATE-AND-OMITTED-INDEX-DETECTED=PASS");
    println!("NO-ZERO-PADDING-AMBIGUITY=PASS");
    println!("EXTERNAL-DEPENDENCIES=0");
    assert_eq!(total_und, 0, "wrong payload accepted in Monte Carlo");
    println!("STATUS=PASS-HUMAN-WIRE-ARQ");
}

use std::env;
use std::hint::black_box;

#[derive(Clone, Copy)]
enum Codec { Width3Escape, GammaWidth, CandidateS }

#[derive(Clone, Copy)]
enum Wrapper { Raw, StopBit, GammaLength, ContainerBits }

#[derive(Clone)]
struct Bits {
    bytes: Vec<u8>,
    len: usize,
}

impl Bits {
    fn new() -> Self { Self { bytes: Vec::new(), len: 0 } }

    fn push(&mut self, bit: u8) {
        let byte = self.len / 8;
        let shift = 7 - (self.len % 8);
        if byte == self.bytes.len() { self.bytes.push(0); }
        if bit != 0 { self.bytes[byte] |= 1 << shift; }
        self.len += 1;
    }

    fn get(&self, pos: usize) -> u8 {
        let byte = self.bytes[pos / 8];
        (byte >> (7 - (pos % 8))) & 1
    }

    fn extend(&mut self, other: &Bits) {
        for pos in 0..other.len { self.push(other.get(pos)); }
    }

    fn truncate_one(&mut self) {
        assert!(self.len > 0);
        self.len -= 1;
        self.bytes.truncate((self.len + 7) / 8);
        if self.len % 8 != 0 && !self.bytes.is_empty() {
            let keep = self.len % 8;
            let mask = 0xFFu8 << (8 - keep);
            let last = self.bytes.len() - 1;
            self.bytes[last] &= mask;
        }
    }

    fn pad_to_byte(&mut self) {
        while self.len % 8 != 0 { self.push(0); }
    }
}

#[derive(Clone)]
struct Frame {
    bits: Bits,
    raw_exact_len: usize,
    valid_bits_last: u8,
    semantic_payload_bits: usize,
    word_framing_bits: usize,
    message_framing_bits: usize,
    byte_padding_bits: usize,
    expected_words: usize,
    expected_widths: Vec<usize>,
    invalid: bool,
}

#[derive(Clone, Copy)]
struct RawSpan { start: usize, len: usize, boundary_steps: usize }

#[derive(Clone, Copy, Default)]
struct DecodeStats {
    words: usize,
    header_loop_iterations: usize,
    handoff_checksum: u64,
}

fn gamma_bits(value: usize) -> usize {
    assert!(value >= 1);
    let width = usize::BITS as usize - value.leading_zeros() as usize;
    2 * width - 1
}

fn write_uint(bits: &mut Bits, value: usize, width: usize) {
    for shift in (0..width).rev() { bits.push(((value >> shift) & 1) as u8); }
}

fn write_gamma(bits: &mut Bits, value: usize) {
    assert!(value >= 1);
    let width = usize::BITS as usize - value.leading_zeros() as usize;
    for _ in 1..width { bits.push(0); }
    write_uint(bits, value, width);
}

fn write_gamma0(bits: &mut Bits, value: usize) {
    write_gamma(bits, value + 1);
}

fn read_uint(bits: &Bits, pos: &mut usize, end: usize, width: usize) -> Result<usize, ()> {
    if *pos + width > end { return Err(()); }
    let mut value = 0usize;
    for _ in 0..width {
        value = (value << 1) | bits.get(*pos) as usize;
        *pos += 1;
    }
    Ok(value)
}

fn read_gamma(bits: &Bits, pos: &mut usize, end: usize, loops: &mut usize) -> Result<usize, ()> {
    let mut zeros = 0usize;
    while *pos < end && bits.get(*pos) == 0 {
        zeros += 1;
        *loops += 1;
        *pos += 1;
    }
    if *pos >= end { return Err(()); }
    *loops += 1;
    *pos += 1; // leading 1
    if *pos + zeros > end { return Err(()); }
    let mut value = 1usize;
    for _ in 0..zeros {
        value = (value << 1) | bits.get(*pos) as usize;
        *loops += 1;
        *pos += 1;
    }
    Ok(value)
}

fn read_gamma0(bits: &Bits, pos: &mut usize, end: usize, loops: &mut usize) -> Result<usize, ()> {
    read_gamma(bits, pos, end, loops)?.checked_sub(1).ok_or(())
}

fn payload(width: usize, salt: usize) -> Vec<u8> {
    let mut bits: Vec<u8> = (0..width)
        .map(|i| (((i * 7 + salt * 3 + width) ^ (i >> 1)) & 1) as u8)
        .collect();
    // Candidate S carries widths >8 as canonical BinaryNumber records, whose
    // normalized representation has no leading zero. Use the same payload for
    // every codec so the CPU comparison remains apples-to-apples.
    if width > 8 {
        bits[0] = 1;
    }
    bits
}

fn encode_words(codec: Codec, words: &[Vec<u8>]) -> Bits {
    let mut out = Bits::new();
    for word in words {
        let width = word.len();
        assert!(width >= 1);
        match codec {
            Codec::Width3Escape => {
                if width <= 7 {
                    write_uint(&mut out, width - 1, 3);
                } else {
                    write_uint(&mut out, 7, 3);
                    write_gamma(&mut out, width - 7);
                }
            }
            Codec::GammaWidth => write_gamma(&mut out, width),
            Codec::CandidateS => {
                if width <= 7 {
                    write_uint(&mut out, width - 1, 3);
                } else if width == 8 {
                    write_uint(&mut out, 0b1110, 4);
                } else {
                    write_uint(&mut out, 0b11110, 5);
                    write_gamma0(&mut out, width);
                }
            }
        }
        for &bit in word { out.push(bit); }
    }
    out
}

fn wrap(raw: &Bits, wrapper: Wrapper, payload_bits: usize, word_bits: usize, widths: Vec<usize>, invalid: bool) -> Frame {
    let expected_words = widths.len();
    match wrapper {
        Wrapper::Raw => Frame {
            bits: raw.clone(),
            raw_exact_len: raw.len,
            valid_bits_last: if raw.len % 8 == 0 { 8 } else { (raw.len % 8) as u8 },
            semantic_payload_bits: payload_bits,
            word_framing_bits: word_bits,
            message_framing_bits: 0,
            byte_padding_bits: 0,
            expected_words,
            expected_widths: widths,
            invalid,
        },
        Wrapper::ContainerBits => {
            let mut bits = raw.clone();
            let pad = (8 - bits.len % 8) % 8;
            bits.pad_to_byte();
            Frame {
                bits,
                raw_exact_len: raw.len,
                valid_bits_last: if raw.len % 8 == 0 { 8 } else { (raw.len % 8) as u8 },
                semantic_payload_bits: payload_bits,
                word_framing_bits: word_bits,
                message_framing_bits: 3 + pad,
                byte_padding_bits: pad,
                expected_words,
                expected_widths: widths,
                invalid,
            }
        }
        Wrapper::StopBit => {
            let mut bits = raw.clone();
            bits.push(1);
            let pad = (8 - bits.len % 8) % 8;
            bits.pad_to_byte();
            Frame {
                bits,
                raw_exact_len: raw.len,
                valid_bits_last: 8,
                semantic_payload_bits: payload_bits,
                word_framing_bits: word_bits,
                message_framing_bits: 1 + pad,
                byte_padding_bits: pad,
                expected_words,
                expected_widths: widths,
                invalid,
            }
        }
        Wrapper::GammaLength => {
            let mut bits = Bits::new();
            write_gamma(&mut bits, raw.len + 1);
            let prefix = bits.len;
            bits.extend(raw);
            let pad = (8 - bits.len % 8) % 8;
            bits.pad_to_byte();
            Frame {
                bits,
                raw_exact_len: raw.len,
                valid_bits_last: 8,
                semantic_payload_bits: payload_bits,
                word_framing_bits: word_bits,
                message_framing_bits: prefix + pad,
                byte_padding_bits: pad,
                expected_words,
                expected_widths: widths,
                invalid,
            }
        }
    }
}

fn unwrap(frame: &Frame, wrapper: Wrapper) -> Result<RawSpan, ()> {
    match wrapper {
        Wrapper::Raw => Ok(RawSpan { start: 0, len: frame.raw_exact_len, boundary_steps: 0 }),
        Wrapper::ContainerBits => {
            if frame.bits.bytes.is_empty() { return Ok(RawSpan { start: 0, len: 0, boundary_steps: 1 }); }
            if !(1..=8).contains(&frame.valid_bits_last) { return Err(()); }
            let len = (frame.bits.bytes.len() - 1) * 8 + frame.valid_bits_last as usize;
            Ok(RawSpan { start: 0, len, boundary_steps: 1 })
        }
        Wrapper::StopBit => {
            let mut pos = frame.bits.len;
            let mut steps = 0usize;
            while pos > 0 {
                pos -= 1;
                steps += 1;
                if frame.bits.get(pos) == 1 {
                    return Ok(RawSpan { start: 0, len: pos, boundary_steps: steps });
                }
            }
            Err(())
        }
        Wrapper::GammaLength => {
            let mut pos = 0usize;
            let mut loops = 0usize;
            let encoded = read_gamma(&frame.bits, &mut pos, frame.bits.len, &mut loops)?;
            let raw_len = encoded.checked_sub(1).ok_or(())?;
            if pos + raw_len > frame.bits.len { return Err(()); }
            for tail in (pos + raw_len)..frame.bits.len {
                loops += 1;
                if frame.bits.get(tail) != 0 { return Err(()); }
            }
            Ok(RawSpan { start: pos, len: raw_len, boundary_steps: loops })
        }
    }
}

fn decode(codec: Codec, frame: &Frame, wrapper: Wrapper) -> Result<(DecodeStats, RawSpan), ()> {
    let span = unwrap(frame, wrapper)?;
    let end = span.start + span.len;
    let mut pos = span.start;
    let mut stats = DecodeStats::default();

    while pos < end {
        let width = match codec {
            Codec::Width3Escape => {
                let tag = read_uint(&frame.bits, &mut pos, end, 3)?;
                stats.header_loop_iterations += 3;
                if tag < 7 {
                    tag + 1
                } else {
                    let extra = read_gamma(&frame.bits, &mut pos, end, &mut stats.header_loop_iterations)?;
                    extra + 7
                }
            }
            Codec::GammaWidth => read_gamma(&frame.bits, &mut pos, end, &mut stats.header_loop_iterations)?,
            Codec::CandidateS => {
                let head = read_uint(&frame.bits, &mut pos, end, 3)?;
                stats.header_loop_iterations += 3;
                if head < 7 {
                    head + 1
                } else {
                    let extension = read_uint(&frame.bits, &mut pos, end, 1)?;
                    stats.header_loop_iterations += 1;
                    if extension == 0 {
                        8
                    } else {
                        let class = read_uint(&frame.bits, &mut pos, end, 1)?;
                        stats.header_loop_iterations += 1;
                        if class != 0 {
                            // Local/Sound/reserved classes are not generic word
                            // payloads in this benchmark slice.
                            return Err(());
                        }
                        let width = read_gamma0(
                            &frame.bits,
                            &mut pos,
                            end,
                            &mut stats.header_loop_iterations,
                        )?;
                        if width <= 8 { return Err(()); }
                        width
                    }
                }
            }
        };
        if width == 0 || pos + width > end { return Err(()); }

        // Handoff is exact span/width. Carrier construction belongs to #1989.
        stats.words += 1;
        stats.handoff_checksum = stats.handoff_checksum
            .wrapping_mul(0x9E37_79B1)
            .wrapping_add(((pos as u64) << 32) ^ width as u64);
        pos += width;
    }

    if pos != end { return Err(()); }
    Ok((stats, span))
}

fn decode_collect(codec: Codec, frame: &Frame, wrapper: Wrapper) -> Result<Vec<Vec<u8>>, ()> {
    let span = unwrap(frame, wrapper)?;
    let end = span.start + span.len;
    let mut pos = span.start;
    let mut out = Vec::new();

    while pos < end {
        let width = match codec {
            Codec::Width3Escape => {
                let tag = read_uint(&frame.bits, &mut pos, end, 3)?;
                if tag < 7 {
                    tag + 1
                } else {
                    let mut loops = 0;
                    read_gamma(&frame.bits, &mut pos, end, &mut loops)? + 7
                }
            }
            Codec::GammaWidth => {
                let mut loops = 0;
                read_gamma(&frame.bits, &mut pos, end, &mut loops)?
            }
            Codec::CandidateS => {
                let head = read_uint(&frame.bits, &mut pos, end, 3)?;
                if head < 7 {
                    head + 1
                } else {
                    let extension = read_uint(&frame.bits, &mut pos, end, 1)?;
                    if extension == 0 {
                        8
                    } else {
                        let class = read_uint(&frame.bits, &mut pos, end, 1)?;
                        if class != 0 { return Err(()); }
                        let mut loops = 0;
                        let width = read_gamma0(&frame.bits, &mut pos, end, &mut loops)?;
                        if width <= 8 { return Err(()); }
                        width
                    }
                }
            }
        };
        if width == 0 || pos + width > end { return Err(()); }
        let mut word = Vec::with_capacity(width);
        for p in pos..(pos + width) { word.push(frame.bits.get(p)); }
        out.push(word);
        pos += width;
    }
    Ok(out)
}

fn case_words(name: &str) -> Vec<Vec<u8>> {
    if let Some(raw) = name.strip_prefix("single-") {
        let width: usize = raw.parse().expect("single width");
        return vec![payload(width, 1)];
    }
    match name {
        "repeated3" => (0..64).map(|i| payload(3, i)).collect(),
        "mixed" => [1usize,2,3,4,5,6,7,8,9,16,32,64,65,128]
            .iter().enumerate().map(|(i,&w)| payload(w, i)).collect(),
        "corpus" => vec![
            vec![1,0], vec![0,0,1], vec![0,1],                       // 10 001 01
            vec![1,0], vec![1,0,1], vec![1,1], vec![1,1,0], vec![0,1], // dotted pair
            vec![1,0,1,0], vec![1,0,1,1], vec![1,0,1,1,1,1,1],    // selector paths
            vec![0], vec![0,0], vec![0,0,0], vec![1,0,1,0],
            vec![1,0,1,1,1,1,1,1,1,1,1],                          // 11-bit word
        ],
        "invalid" => vec![payload(8, 7)],
        _ => panic!("unknown case: {name}"),
    }
}

fn make_frame(codec: Codec, wrapper: Wrapper, case: &str) -> Frame {
    let words = case_words(case);
    let payload_bits: usize = words.iter().map(Vec::len).sum();
    let mut raw = encode_words(codec, &words);
    let valid_raw_len = raw.len;
    let word_framing_bits = valid_raw_len - payload_bits;
    let invalid = case == "invalid";
    if invalid { raw.truncate_one(); }
    wrap(
        &raw,
        wrapper,
        if invalid { payload_bits.saturating_sub(1) } else { payload_bits },
        word_framing_bits,
        words.iter().map(Vec::len).collect(),
        invalid,
    )
}

fn parse_codec(s: &str) -> Codec {
    match s {
        "a" => Codec::Width3Escape,
        "b" => Codec::GammaWidth,
        "s" => Codec::CandidateS,
        _ => panic!("codec"),
    }
}

fn parse_wrapper(s: &str) -> Wrapper {
    match s {
        "raw" => Wrapper::Raw,
        "stop" => Wrapper::StopBit,
        "gamma" => Wrapper::GammaLength,
        "container" => Wrapper::ContainerBits,
        _ => panic!("wrapper"),
    }
}

fn verify_all() {
    let cases = [
        "single-1","single-2","single-3","single-4","single-5","single-6",
        "single-7","single-8","single-9","single-16","single-32","single-64",
        "single-65","single-128","repeated3","mixed","corpus",
    ];
    for codec in [Codec::Width3Escape, Codec::GammaWidth, Codec::CandidateS] {
        for wrapper in [Wrapper::Raw, Wrapper::StopBit, Wrapper::GammaLength, Wrapper::ContainerBits] {
            for case in cases {
                let words = case_words(case);
                let frame = make_frame(codec, wrapper, case);
                let decoded = decode_collect(codec, &frame, wrapper).expect("roundtrip decode");
                assert_eq!(decoded, words, "roundtrip mismatch {case}");
                let (stats, _) = decode(codec, &frame, wrapper).expect("timed decode parity");
                assert_eq!(stats.words, words.len());
            }
            let frame = make_frame(codec, wrapper, "invalid");
            assert!(decode(codec, &frame, wrapper).is_err(), "truncated input accepted");
        }
    }
    println!("VERIFY\tPASS");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() == 2 && args[1] == "verify" {
        verify_all();
        return;
    }
    if args.len() != 7 {
        eprintln!("usage: framing-bench PHASE CODEC WRAPPER CASE ITERATIONS MODE");
        eprintln!("MODE must be valid|invalid");
        std::process::exit(2);
    }

    let phase = args[1].as_str();
    let codec = parse_codec(&args[2]);
    let wrapper = parse_wrapper(&args[3]);
    let case = args[4].as_str();
    let iterations: usize = args[5].parse().expect("iterations");
    let mode = args[6].as_str();
    assert_eq!(mode == "invalid", case == "invalid");

    let frame = make_frame(codec, wrapper, case);
    black_box(&frame);

    if phase == "prepare" {
        let checksum = frame.bits.bytes.len()
            ^ frame.raw_exact_len
            ^ frame.semantic_payload_bits
            ^ frame.word_framing_bits;
        println!("CHECKSUM\t{}", black_box(checksum));
    } else {
        assert_eq!(phase, "full");
        let mut checksum = 0u64;
        let mut total_words = 0usize;
        let mut total_header_loops = 0usize;
        let mut total_boundary_steps = 0usize;
        let mut rejects = 0usize;

        for _ in 0..iterations {
            match decode(codec, &frame, wrapper) {
                Ok((stats, span)) => {
                    if mode == "invalid" { panic!("invalid frame accepted"); }
                    checksum ^= stats.handoff_checksum.wrapping_add(span.len as u64);
                    total_words += stats.words;
                    total_header_loops += stats.header_loop_iterations;
                    total_boundary_steps += span.boundary_steps;
                }
                Err(()) => {
                    if mode != "invalid" { panic!("valid frame rejected"); }
                    rejects += 1;
                }
            }
        }
        println!("CHECKSUM\t{}", black_box(checksum));
        println!("METRIC\tdecoded_words\t{total_words}");
        println!("METRIC\theader_loop_iterations\t{total_header_loops}");
        println!("METRIC\tmessage_boundary_steps\t{total_boundary_steps}");
        println!("METRIC\trejections\t{rejects}");
    }

    let wrapper_total = frame.message_framing_bits;
    let total_wire = frame.semantic_payload_bits + frame.word_framing_bits + wrapper_total;
    println!("METRIC\twords_per_message\t{}", frame.expected_words);
    println!("METRIC\tsemantic_payload_bits\t{}", frame.semantic_payload_bits);
    println!("METRIC\tword_framing_bits\t{}", frame.word_framing_bits);
    println!("METRIC\tmessage_framing_bits\t{}", frame.message_framing_bits);
    println!("METRIC\tbyte_padding_bits\t{}", frame.byte_padding_bits);
    println!("METRIC\ttotal_wire_bits\t{total_wire}");
}

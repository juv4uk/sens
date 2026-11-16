fn fib(n: u64) -> u64 {
    if n < 2 {
        return n;
    }
    fib(n - 1) + fib(n - 2)
}

fn sieve(n: usize) -> usize {
    let mut comp = vec![false; n + 1];
    let mut i = 2usize;
    while i * i <= n {
        if !comp[i] {
            let mut j = i * i;
            while j <= n {
                comp[j] = true;
                j += i;
            }
        }
        i += 1;
    }
    let mut count = 0usize;
    let mut k = 2usize;
    while k <= n {
        if !comp[k] {
            count += 1;
        }
        k += 1;
    }
    count
}

fn collatz(n: u64) -> u64 {
    let mut total = 0u64;
    let mut i = 1u64;
    while i <= n {
        let mut x = i;
        while x != 1 {
            x = if x % 2 == 0 { x / 2 } else { 3 * x + 1 };
            total += 1;
        }
        i += 1;
    }
    total
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let fib_n: u64 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(35);
    let sieve_n: usize = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(10_000_000);
    let col_n: u64 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(1_000_000);

    println!("fib({}) = {}", fib_n, fib(fib_n));
    println!("sieve({}) = {}", sieve_n, sieve(sieve_n));
    println!("collatz({}) = {}", col_n, collatz(col_n));
}

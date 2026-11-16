import Foundation

@inline(never)
func fib(_ n: Int) -> Int {
    if n < 2 { return n }
    return fib(n - 1) + fib(n - 2)
}

func sieve(_ n: Int) -> Int {
    var comp = [Bool](repeating: false, count: n + 1)
    var i = 2
    while i * i <= n {
        if !comp[i] {
            var j = i * i
            while j <= n {
                comp[j] = true
                j += i
            }
        }
        i += 1
    }
    var count = 0
    var k = 2
    while k <= n {
        if !comp[k] { count += 1 }
        k += 1
    }
    return count
}

func collatz(_ n: Int) -> Int {
    var total = 0
    var i = 1
    while i <= n {
        var x = i
        while x != 1 {
            x = (x % 2 == 0) ? x / 2 : 3 * x + 1
            total += 1
        }
        i += 1
    }
    return total
}

@main
struct Bench {
    static func main() {
        let args = CommandLine.arguments
        let fibN = args.count > 1 ? Int(args[1])! : 35
        let sieveN = args.count > 2 ? Int(args[2])! : 10_000_000
        let colN = args.count > 3 ? Int(args[3])! : 1_000_000

        print("fib(\(fibN)) = \(fib(fibN))")
        print("sieve(\(sieveN)) = \(sieve(sieveN))")
        print("collatz(\(colN)) = \(collatz(colN))")
    }
}

function fib(n::Int64)
    n < 2 && return n
    return fib(n - 1) + fib(n - 2)
end

function sieve(n::Int)
    comp = zeros(UInt8, n + 1)
    i = 2
    while i * i <= n
        if comp[i] == 0
            j = i * i
            while j <= n
                comp[j] = 1
                j += i
            end
        end
        i += 1
    end
    count = 0
    k = 2
    while k <= n
        if comp[k] == 0
            count += 1
        end
        k += 1
    end
    return count
end

function collatz(n::Int64)
    total = Int64(0)
    i = Int64(1)
    while i <= n
        x = i
        while x != 1
            x = (x % 2 == 0) ? x ÷ 2 : 3 * x + 1
            total += 1
        end
        i += 1
    end
    return total
end

fibN = length(ARGS) >= 1 ? parse(Int64, ARGS[1]) : 35
sieveN = length(ARGS) >= 2 ? parse(Int, ARGS[2]) : 10000000
colN = length(ARGS) >= 3 ? parse(Int64, ARGS[3]) : 1000000

println("fib($fibN) = ", fib(fibN))
println("sieve($sieveN) = ", sieve(sieveN))
println("collatz($colN) = ", collatz(colN))

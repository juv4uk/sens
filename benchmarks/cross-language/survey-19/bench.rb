def fib(n)
  return n if n < 2
  fib(n - 1) + fib(n - 2)
end

def sieve(n)
  comp = Array.new(n + 1, false)
  i = 2
  while i * i <= n
    unless comp[i]
      j = i * i
      while j <= n
        comp[j] = true
        j += i
      end
    end
    i += 1
  end
  count = 0
  k = 2
  while k <= n
    count += 1 unless comp[k]
    k += 1
  end
  count
end

def collatz(n)
  total = 0
  i = 1
  while i <= n
    x = i
    while x != 1
      x = x.even? ? x / 2 : 3 * x + 1
      total += 1
    end
    i += 1
  end
  total
end

fib_n = ARGV[0] ? ARGV[0].to_i : 35
sieve_n = ARGV[1] ? ARGV[1].to_i : 10_000_000
col_n = ARGV[2] ? ARGV[2].to_i : 1_000_000

puts "fib(#{fib_n}) = #{fib(fib_n)}"
puts "sieve(#{sieve_n}) = #{sieve(sieve_n)}"
puts "collatz(#{col_n}) = #{collatz(col_n)}"

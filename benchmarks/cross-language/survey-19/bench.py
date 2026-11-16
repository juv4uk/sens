import sys

def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

def sieve(n):
    comp = bytearray(n + 1)
    i = 2
    while i * i <= n:
        if not comp[i]:
            j = i * i
            while j <= n:
                comp[j] = 1
                j += i
        i += 1
    count = 0
    k = 2
    while k <= n:
        if not comp[k]:
            count += 1
        k += 1
    return count

def collatz(n):
    total = 0
    i = 1
    while i <= n:
        x = i
        while x != 1:
            x = x // 2 if x % 2 == 0 else 3 * x + 1
            total += 1
        i += 1
    return total

fibN = int(sys.argv[1]) if len(sys.argv) > 1 else 35
sieveN = int(sys.argv[2]) if len(sys.argv) > 2 else 10000000
colN = int(sys.argv[3]) if len(sys.argv) > 3 else 1000000

print("fib(%d) = %d" % (fibN, fib(fibN)))
print("sieve(%d) = %d" % (sieveN, sieve(sieveN)))
print("collatz(%d) = %d" % (colN, collatz(colN)))

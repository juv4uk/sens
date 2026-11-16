package main

import (
	"fmt"
	"os"
	"strconv"
)

func fib(n uint64) uint64 {
	if n < 2 {
		return n
	}
	return fib(n-1) + fib(n-2)
}

func sieve(n int) int {
	comp := make([]byte, n+1)
	for i := 2; i*i <= n; i++ {
		if comp[i] == 0 {
			for j := i * i; j <= n; j += i {
				comp[j] = 1
			}
		}
	}
	count := 0
	for k := 2; k <= n; k++ {
		if comp[k] == 0 {
			count++
		}
	}
	return count
}

func collatz(n uint64) uint64 {
	var total uint64
	for i := uint64(1); i <= n; i++ {
		x := i
		for x != 1 {
			if x%2 == 0 {
				x /= 2
			} else {
				x = 3*x + 1
			}
			total++
		}
	}
	return total
}

func arg(idx int, def uint64) uint64 {
	if len(os.Args) > idx {
		if v, err := strconv.ParseUint(os.Args[idx], 10, 64); err == nil {
			return v
		}
	}
	return def
}

func main() {
	fibN := arg(1, 35)
	sieveN := arg(2, 10000000)
	colN := arg(3, 1000000)

	fmt.Printf("fib(%d) = %d\n", fibN, fib(fibN))
	fmt.Printf("sieve(%d) = %d\n", sieveN, sieve(int(sieveN)))
	fmt.Printf("collatz(%d) = %d\n", colN, collatz(colN))
}

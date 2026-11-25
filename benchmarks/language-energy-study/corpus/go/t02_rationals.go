// T02 exact rational sum: independent Go implementation for ENERGY-02 (#6287).
// Physical cross-language parity only; SENS owns its language semantics.
// Run: TASK_ID=T02-exact-rationals TASK_N=20 go run t02_rationals.go
package main

import (
	"errors"
	"fmt"
	"math/big"
	"os"
	"strconv"
)

const taskID = "T02-exact-rationals"
const maxN = 1000 // Finite research workload budget; frozen MEASURE_SIZE is N=400.

func parseInput(id, raw string) (int, error) {
	if id != taskID {
		return 0, errors.New("TASK_ID must be T02-exact-rationals")
	}
	if len(raw) == 0 || len(raw) > 4 || raw[0] == '0' {
		return 0, errors.New("TASK_N must be canonical positive decimal")
	}
	for _, ch := range raw {
		if ch < '0' || ch > '9' {
			return 0, errors.New("TASK_N must contain only ASCII decimal digits")
		}
	}
	n, err := strconv.Atoi(raw)
	if err != nil || n < 1 || n > maxN {
		return 0, fmt.Errorf("TASK_N must be within 1..%d", maxN)
	}
	return n, nil
}

func harmonic(n int) *big.Rat {
	total := new(big.Rat)
	term := new(big.Rat)
	numerator := big.NewInt(1)
	denominator := new(big.Int)
	for k := 1; k <= n; k++ {
		denominator.SetInt64(int64(k))
		term.SetFrac(numerator, denominator)
		total.Add(total, term)
	}
	return total // math/big.Rat retains a normalized numerator/denominator.
}

func run(id, raw string) (string, error) {
	n, err := parseInput(id, raw)
	if err != nil {
		return "", err
	}
	result := harmonic(n)
	// Always emit P/Q (including 1/1); RatString() would omit /1.
	return result.Num().String() + "/" + result.Denom().String(), nil
}

func main() {
	output, err := run(os.Getenv("TASK_ID"), os.Getenv("TASK_N"))
	if err != nil {
		fmt.Fprintln(os.Stderr, "T02_INPUT_REJECTED:", err)
		os.Exit(2)
	}
	fmt.Println(output) // One and only one stdout line.
}

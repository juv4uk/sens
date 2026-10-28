package main

import (
	"math/big"
	"strings"
	"testing"
)

func TestExactKnownFractions(t *testing.T) {
	cases := []struct {
		n, expected string
	}{
		{"1", "1/1"},
		{"2", "3/2"},
		{"3", "11/6"},
		{"4", "25/12"},
		{"6", "49/20"},
	}
	for _, tc := range cases {
		got, err := run(taskID, tc.n)
		if err != nil || got != tc.expected {
			t.Fatalf("N=%s: got=%q, err=%v; want=%q", tc.n, got, err, tc.expected)
		}
	}
}

func TestReducedAndPositive(t *testing.T) {
	for _, n := range []int{20, 400} {
		r := harmonic(n)
		gcd := new(big.Int).GCD(nil, nil, r.Num(), r.Denom())
		if gcd.Cmp(big.NewInt(1)) != 0 || r.Sign() < 1 || r.Denom().Sign() < 1 {
			t.Fatalf("N=%d is not a positive reduced fraction", n)
		}
	}
}

func TestStrictMonotonicity(t *testing.T) {
	for n := 2; n <= 20; n++ {
		if harmonic(n).Cmp(harmonic(n-1)) <= 0 {
			t.Fatalf("N=%d did not increase", n)
		}
	}
}

func TestInputRejected(t *testing.T) {
	for _, tc := range []struct{ id, n string }{
		{"", "20"}, {"T01-symbolic-recursion", "20"},
		{taskID, ""}, {taskID, "0"}, {taskID, "01"},
		{taskID, "-1"}, {taskID, "+2"}, {taskID, "2.0"},
		{taskID, " 20"}, {taskID, "20 "}, {taskID, "2\n"},
		{taskID, "٤"}, {taskID, "1001"}, {taskID, "999999999"},
	} {
		if output, err := run(tc.id, tc.n); err == nil || output != "" {
			t.Fatalf("accepted invalid id=%q N=%q: %q, %v", tc.id, tc.n, output, err)
		}
	}
}

func TestExactOutputFormat(t *testing.T) {
	for _, n := range []string{"1", "20", "400"} {
		output, err := run(taskID, n)
		if err != nil || strings.Count(output, "/") != 1 || strings.Contains(output, "\n") {
			t.Fatalf("non-canonical fraction N=%s: %q, %v", n, output, err)
		}
	}
}

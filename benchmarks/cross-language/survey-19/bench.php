<?php

function fib(int $n): int
{
    if ($n < 2) return $n;
    return fib($n - 1) + fib($n - 2);
}

function sieve(int $n): int
{
    $comp = str_repeat("\0", $n + 1);
    for ($i = 2; $i * $i <= $n; $i++) {
        if ($comp[$i] === "\0") {
            for ($j = $i * $i; $j <= $n; $j += $i) {
                $comp[$j] = "\1";
            }
        }
    }
    $count = 0;
    for ($k = 2; $k <= $n; $k++) {
        if ($comp[$k] === "\0") $count++;
    }
    return $count;
}

function collatz(int $n): int
{
    $total = 0;
    for ($i = 1; $i <= $n; $i++) {
        $x = $i;
        while ($x != 1) {
            $x = ($x % 2 === 0) ? intdiv($x, 2) : 3 * $x + 1;
            $total++;
        }
    }
    return $total;
}

$fibN = $argc > 1 ? (int) $argv[1] : 35;
$sieveN = $argc > 2 ? (int) $argv[2] : 10000000;
$colN = $argc > 3 ? (int) $argv[3] : 1000000;

printf("fib(%d) = %d\n", $fibN, fib($fibN));
printf("sieve(%d) = %d\n", $sieveN, sieve($sieveN));
printf("collatz(%d) = %d\n", $colN, collatz($colN));

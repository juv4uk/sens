using System;

internal static class Bench
{
    private static long Fib(long n) => n < 2 ? n : Fib(n - 1) + Fib(n - 2);

    private static long Sieve(int n)
    {
        byte[] comp = new byte[n + 1];
        for (int i = 2; (long)i * i <= n; i++)
        {
            if (comp[i] == 0)
            {
                for (long j = (long)i * i; j <= n; j += i)
                {
                    comp[(int)j] = 1;
                }
            }
        }
        long count = 0;
        for (int k = 2; k <= n; k++)
        {
            if (comp[k] == 0) count++;
        }
        return count;
    }

    private static long Collatz(long n)
    {
        long total = 0;
        for (long i = 1; i <= n; i++)
        {
            long x = i;
            while (x != 1)
            {
                x = (x % 2 == 0) ? x / 2 : 3 * x + 1;
                total++;
            }
        }
        return total;
    }

    private static void Main(string[] args)
    {
        long fibN = args.Length > 0 ? long.Parse(args[0]) : 35;
        int sieveN = args.Length > 1 ? int.Parse(args[1]) : 10000000;
        long colN = args.Length > 2 ? long.Parse(args[2]) : 1000000;

        Console.WriteLine($"fib({fibN}) = {Fib(fibN)}");
        Console.WriteLine($"sieve({sieveN}) = {Sieve(sieveN)}");
        Console.WriteLine($"collatz({colN}) = {Collatz(colN)}");
    }
}

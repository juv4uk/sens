public class Bench {
    static long fib(long n) {
        if (n < 2) return n;
        return fib(n - 1) + fib(n - 2);
    }

    static long sieve(int n) {
        byte[] comp = new byte[n + 1];
        for (int i = 2; (long) i * i <= n; i++) {
            if (comp[i] == 0) {
                for (long j = (long) i * i; j <= n; j += i) {
                    comp[(int) j] = 1;
                }
            }
        }
        long count = 0;
        for (int k = 2; k <= n; k++) {
            if (comp[k] == 0) count++;
        }
        return count;
    }

    static long collatz(long n) {
        long total = 0;
        for (long i = 1; i <= n; i++) {
            long x = i;
            while (x != 1) {
                x = (x % 2 == 0) ? x / 2 : 3 * x + 1;
                total++;
            }
        }
        return total;
    }

    public static void main(String[] args) {
        long fibN = args.length > 0 ? Long.parseLong(args[0]) : 35;
        int sieveN = args.length > 1 ? Integer.parseInt(args[1]) : 10000000;
        long colN = args.length > 2 ? Long.parseLong(args[2]) : 1000000;

        System.out.println("fib(" + fibN + ") = " + fib(fibN));
        System.out.println("sieve(" + sieveN + ") = " + sieve(sieveN));
        System.out.println("collatz(" + colN + ") = " + collatz(colN));
    }
}

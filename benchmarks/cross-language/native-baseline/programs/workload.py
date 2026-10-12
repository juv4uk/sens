import sys

n = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
acc = sum(i * i for i in range(n + 1))
print(acc)

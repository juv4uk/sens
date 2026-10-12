import sys

def tree(depth, seed):
    if depth == 0:
        return seed
    left = tree(depth - 1, seed * 3 + 1)
    right = tree(depth - 1, seed * 3 + 2)
    return left ^ (right + depth)

depth = int(sys.argv[1]) if len(sys.argv) > 1 else 18
print(tree(depth, 1))

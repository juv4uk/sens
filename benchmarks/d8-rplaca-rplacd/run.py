#!/usr/bin/env python3
"""Tiny research witness for #3943: mutation != reconstruction."""

class Cell:
    def __init__(self, head, tail):
        self.head = head
        self.tail = tail

def rplaca(cell, value):
    cell.head = value
    return cell

def rplacd(cell, value):
    cell.tail = value
    return cell

def persistent_replace_head(cell, value):
    return Cell(value, cell.tail)

def persistent_replace_tail(cell, value):
    return Cell(cell.head, value)

def main():
    p = Cell('a', 'b')
    q = p
    assert rplaca(p, 'x') is p
    assert q.head == 'x' and q.tail == 'b'
    assert rplacd(p, 'y') is p
    assert q.head == 'x' and q.tail == 'y'

    p2 = Cell('a', 'b')
    q2 = p2
    rebuilt = persistent_replace_head(p2, 'x')
    assert rebuilt is not p2
    assert q2.head == 'a', 'persistent reconstruction must not mutate alias'
    rebuilt2 = persistent_replace_tail(p2, 'y')
    assert rebuilt2 is not p2
    assert q2.tail == 'b', 'persistent reconstruction must not mutate alias'

    print('RPLACA/RPLACD alias witness: PASS')

if __name__ == '__main__':
    main()

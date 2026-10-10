#!/usr/bin/env python3
"""Дослідний носій T21/T22/T33 для тритів без 22; НЕ формат .sens.

Контракт: потік складається ТІЛЬКИ з повних блоків відомої тритової довжини.
Довжина, версія й перевірка цілісності належать зовнішньому конверту.
Семантична влада D1–D9, T5 і чинні .sens залишаються незмінними.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import statistics
import time
from pathlib import Path

LIMIT = 1 << 32
F = [1, 3]
for _ in range(2, 34):
    F.append(2 * F[-1] + 2 * F[-2])
ESCAPES = (F[22] - LIMIT + 254) // 255
DIRECT = LIMIT - ESCAPES


def ways(left: int, previous_two: bool) -> int:
    if left == 0:
        return 1
    return 2 * F[left - 1] if previous_two else F[left]


def rank(trits: str) -> int:
    if not trits or len(trits) > 33 or any(t not in '012' for t in trits):
        raise ValueError('некоректний тритовий рядок')
    result = 0
    previous_two = False
    for i, symbol in enumerate(trits):
        digit = ord(symbol) - 48
        if previous_two and digit == 2:
            raise ValueError('заборонена пара 22')
        for smaller in range(digit):
            if not (previous_two and smaller == 2):
                result += ways(len(trits) - i - 1, smaller == 2)
        previous_two = digit == 2
    return result


def unrank(length: int, value: int) -> str:
    if length not in (21, 22, 33) or not 0 <= value < F[length]:
        raise ValueError('недопустима довжина або ранг')
    previous_two = False
    output = []
    for left in range(length - 1, -1, -1):
        for digit in range(3):
            if previous_two and digit == 2:
                continue
            count = ways(left, digit == 2)
            if value < count:
                output.append(str(digit))
                previous_two = digit == 2
                break
            value -= count
        else:
            raise AssertionError('зламане ранжування')
    return ''.join(output)


def encode_block(trits: str) -> bytes:
    length = len(trits)
    if length not in (21, 22, 33):
        raise ValueError('підтримано лише повні блоки 21/22/33')
    number = rank(trits)
    if length == 22 and number >= DIRECT:
        suffix = number - DIRECT
        return (DIRECT + suffix // 256).to_bytes(4, 'big') + bytes([suffix % 256])
    return number.to_bytes(6 if length == 33 else 4, 'big')


def decode_block(data: bytes, length: int) -> str:
    if length not in (21, 22, 33):
        raise ValueError('непідтримана тритова довжина')
    if length in (21, 33):
        if len(data) != (6 if length == 33 else 4):
            raise ValueError('неправильна кількість байтів')
        number = int.from_bytes(data, 'big')
    else:
        if len(data) not in (4, 5):
            raise ValueError('неправильна кількість байтів')
        prefix = int.from_bytes(data[:4], 'big')
        if prefix < DIRECT:
            if len(data) != 4:
                raise ValueError('непотрібне розширення')
            number = prefix
        else:
            if len(data) != 5:
                raise ValueError('обрізане розширення')
            number = DIRECT + (prefix - DIRECT) * 256 + data[4]
    if number >= F[length]:
        raise ValueError('незайнятий або неканонічний код')
    return unrank(length, number)


def encode_stream(trits: str, width: int) -> bytes:
    if width not in (21, 22, 33) or len(trits) % width:
        raise ValueError('довжина мусить бути кратною ширині')
    if '22' in trits:
        raise ValueError('порушення 22, зокрема між блоками')
    return b''.join(encode_block(trits[i:i + width]) for i in range(0, len(trits), width))


def decode_stream(data: bytes, width: int, ntrits: int) -> str:
    if width not in (21, 22, 33) or ntrits < 0 or ntrits % width:
        raise ValueError('некоректна метаінформація потоку')
    offset = 0
    output = []
    for _ in range(ntrits // width):
        if width != 22:
            size = 6 if width == 33 else 4
        else:
            if len(data) - offset < 4:
                raise ValueError('обрізаний заголовок блока')
            prefix = int.from_bytes(data[offset:offset + 4], 'big')
            size = 4 if prefix < DIRECT else 5
        if offset + size > len(data):
            raise ValueError('обрізаний блок')
        output.append(decode_block(data[offset:offset + size], width))
        offset += size
    if offset != len(data):
        raise ValueError('зайві байти в потоці')
    result = ''.join(output)
    if '22' in result:
        raise ValueError('заборонена пара на межі блоків')
    if encode_stream(result, width) != data:
        raise ValueError('неканонічне представлення')
    return result


def fixture(ntrits: int, seed: int = 20261010) -> str:
    rng = random.Random(seed)
    digits = []
    previous_two = False
    for _ in range(ntrits):
        digit = rng.randrange(2 if previous_two else 3)
        digits.append(str(digit))
        previous_two = digit == 2
    return ''.join(digits)


def verify() -> int:
    if not __debug__:
        raise RuntimeError('Python -O вимикає assert: перевірку заблоковано')
    checks = 0
    rng = random.Random(22)
    assert F[21] == 1_579_869_184 and F[22] == 4_316_282_880
    assert F[33] == 273_203_580_829_696 and ESCAPES == 83_591
    assert DIRECT + ESCAPES == LIMIT
    for length in (21, 22, 33):
        for v in {0, 1, F[length] // 2, F[length] - 1, *(rng.randrange(F[length]) for _ in range(3000))}:
            x = unrank(length, v)
            assert rank(x) == v
            assert decode_block(encode_block(x), length) == x
            checks += 1
        try:
            decode_block((F[length]).to_bytes(6 if length == 33 else 5 if length == 22 else 4, 'big'), length)
        except ValueError:
            pass
        else:
            if length != 22:
                raise AssertionError('декодер приймає порожній код')
    # Недопустимі довжини, обрізаний escape, зайва п’ята октета та незайнятий ранг.
    for payload, width in (
        (F[21].to_bytes(4, 'big'), 21),
        (F[33].to_bytes(6, 'big'), 33),
        (DIRECT.to_bytes(4, 'big'), 22),
        ((DIRECT - 1).to_bytes(4, 'big') + bytes([0]), 22),
        (bytes([255]) * 5, 22),
        (DIRECT.to_bytes(4, 'big') + bytes([0]), 21),
    ):
        try:
            decode_block(payload, width)
        except ValueError:
            checks += 1
        else:
            raise AssertionError('неправильний код декодовано')
    # Кожна межа escape-регіону, у тому числі найбільший допустимий ранг.
    for v in (DIRECT - 1, DIRECT, DIRECT + 1, LIMIT - 1, LIMIT, F[22] - 1):
        assert decode_block(encode_block(unrank(22, v)), 22) == unrank(22, v)
        checks += 1
    for width in (21, 22, 33):
        source = fixture(4620)
        data = encode_stream(source, width)
        assert decode_stream(data, width, len(source)) == source
        for broken in (data[:-1], data + b'\x00'):
            try:
                decode_stream(broken, width, len(source))
            except ValueError:
                pass
            else:
                raise AssertionError('обрізання/надлишок не відхилено')
        checks += 3
    for width in (21, 22, 33):
        cross = '0' * (width - 1) + '2' + '2' + '0' * (width - 1)
        try:
            encode_stream(cross, width)
        except ValueError:
            checks += 1
        else:
            raise AssertionError('межа блоків допускає 22')
    print(json.dumps({'стан':'PASS','перевірок':checks,'f21':F[21],'f22':F[22],
                      'f33':F[33],'префіксів_розширення':ESCAPES}, ensure_ascii=False))
    return checks


def bench(ntrits: int, reps: int, output: Path | None) -> None:
    if ntrits <= 0 or ntrits % 462 or reps < 3:
        raise ValueError('кількість тритів кратна 462, повторів щонайменше 3')
    verify()
    trits = fixture(ntrits)
    rows = []
    for width in (21, 22, 33):
        samples_encode, samples_decode = [], []
        payload = encode_stream(trits, width)
        for _ in range(reps + 3):
            t0 = time.perf_counter_ns()
            result = encode_stream(trits, width)
            t1 = time.perf_counter_ns()
            restored = decode_stream(result, width, len(trits))
            t2 = time.perf_counter_ns()
            if restored != trits or result != payload:
                raise AssertionError('паритет порушено — виміри недопустимі')
            if len(samples_encode) < reps and _ >= 3:
                samples_encode.append(t1 - t0)
                samples_decode.append(t2 - t1)
        def metrics(samples):
            sorted_ = sorted(samples)
            return {'median_ns':statistics.median(samples),
                    'p95_ns':sorted_[(95 * (len(sorted_) - 1) + 99) // 100],
                    'raw_ns':samples}
        rows.append({'width':width,'bytes':len(payload),'blocks':ntrits // width,
                     'encode':metrics(samples_encode),'decode':metrics(samples_decode)})
    report = {'schema':'sens-enumerative-carrier-research-v1','scope':'Python-кодек, не VM/GPU',
              'python':platform.python_version(),'platform':platform.platform(),
              'ntrits':ntrits,'reps':reps,
              'sha256_trits':hashlib.sha256(trits.encode('ascii')).hexdigest(),
              'rows':rows}
    if output:
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False))
    for r in rows:
        print(f"T{r['width']}: {r['bytes']} Б, enc {r['encode']['median_ns']} нс, "
              f"dec {r['decode']['median_ns']} нс")


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--verify',action='store_true')
    p.add_argument('--bench',action='store_true')
    p.add_argument('--ntrits',type=int,default=4620)
    p.add_argument('--reps',type=int,default=15)
    p.add_argument('--out',type=Path)
    args=p.parse_args()
    if args.bench:
        bench(args.ntrits,args.reps,args.out)
    else:
        verify()

# #1980 незалежна перевірка EOS — GPT-5.6 Sol

Цю реалізацію написано за описами в задачах #1971 і #1980.
Вона не читала `scripts/research-1971-unique-decoding.py`.

Межі перевірки:
- кожне двійкове слово ширини 1..4;
- кожна послідовність із 0..3 таких слів;
- 27 931 послідовність разом із порожньою;
- строгий decoder перевірено на кожному сирому бітовому рядку довжини 0..16.

Кандидат A:
- ширини 1..7: 3-бітний header = width-1;
- ширші слова: `111` + Elias-gamma(width-7);
- після header іде payload.

Кандидат B:
- Elias-gamma(width);
- після header іде payload.

Результати:

```text
A width3+escape
  sequences=27931
  roundtrip_fail=0
  raw_collisions=0
  strict_noncanonical_accepted=0
  zero_padding_misread=26390
  zero_padding_shared_wires=386
  stop_bit_misread=0
  gamma_length_prefix_misread=0

B gamma-only
  sequences=27931
  roundtrip_fail=0
  raw_collisions=0
  strict_noncanonical_accepted=0
  zero_padding_misread=20602
  zero_padding_shared_wires=0
  stop_bit_misread=0
  gamma_length_prefix_misread=0
```

Слова racanā2 `00 01 10 11`, включно з крапкою `11`, проходять round-trip як звичайні payload-слова в обох envelope.

## Незалежний висновок

Опубліковані в #1980 числа відтворюються точно незалежним encoder/decoder.

Звичайне доповнення нулями до межі байта не є механізмом EOS. Неоднозначність/помилка належить межі **контейнера повідомлення**, а не семантичній identity слова.

Stop-bit або явна meaningful-bit length усувають проблему в цій bounded перевірці, не забираючи жодного слова мови.

## Простіший кандидат C для наступної перевірки

Якщо зовнішній transport уже задає межу байтового повідомлення, внутрішньому bitstream не обов'язково бути self-terminating. Контейнер може нести лише:

```text
payload bytes
+ valid bits in final byte   (1..8)
```

або еквівалентно повну meaningful bit length.

Це transport metadata, а не слово SENS. Його варто порівняти з:
- suffix stop bit;
- gamma total-length prefix.

Корисний закон:

```text
word codec owns word decoding
message container owns end-of-stream
```

Self-termination варто вимагати лише для каналів, які справді не мають зовнішньої межі повідомлення.

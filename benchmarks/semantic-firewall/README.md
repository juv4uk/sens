# Semantic Firewall Tournament

Це негативний benchmark для semantic sovereignty.

Він бере canonical `lib/surface/semantic-registry.lisp` і запускає вісім контрольованих мутацій:

- неправильна ширина identity;
- дублювання identity;
- порушення порядку identity;
- вилучення першої хвилі `sa` surface;
- human surface, що маскується під символ;
- невідома namespace;
- обрізаний registry;
- зайвий surface slot.

Кожна мутація **має бути відхилена** canonical checker-ом. Якщо хоча б одна проходить, benchmark завершується помилкою.

```bash
python3 benchmarks/semantic-firewall/run.py \
  --out /tmp/semantic-firewall
cat /tmp/semantic-firewall/report.md
```

Це доказ покриття названих негативних контролів на рівні source checker-а. Він не є загальним security proof і не доводить, що runtime ніколи не має іншого шляху обходу.

# Релізний чекпоінт · F6/Core4 canonical remint · 25.10.2026

## Українська — поточний доказ

Цей документ запускає новий CI **після** автоматичного канонічного remint-коміту, щоб результати перевіряли фізичні артефакти, а не попередній SHA.

- Джерело SENS F6: `lib/lisp-fs.lisp`, blob `dbd5120fa7411b6360aecc6a1b99e1bea2c2af5a`.
- Фізична T5M пара після remint: `lib/lisp-fs.sens`, blob `71f2ccc942737e79bf277e3eeb6626ec10eb22e2`.
- Читабельний бітовий перегляд: `lib/lisp-fs`, blob `0f829cf847f9517d9cc5722beb9fbc27f26b6a53`.
- Producer SENS: `tests/fixtures/wsm-fs-record-producer.lisp`, blob `da1fd0930e455f442f925c248f76f7ecd565115e`.
- Producer T5M: `tests/fixtures/wsm-fs-record-producer.sens`, blob `c9cbbf0f5469d0a9a9cc3bd8116e229f61bc9fc7`; view `tests/fixtures/wsm-fs-record-producer`, blob `c673ca5280dd94811979cf4af95af6cf2c0b2bc3`.
- Автоматичний remint-коміт бібліотеки: `847754bbc980468a980c8a5ba069dae5888ad52b`.
- Остання source-зміна, що просить remint producer: `9995ed710bb07539447fe7e5649a697623ef1ee4`.
- F6 старий точний RED був `F6_RECORD_TYPE expected=String-or-Text7 actual=DomainIdentity`, run `40231059198` на старому SHA `7d648f4646c56803d727c868dc010dfd6daa6b3b`. Це не результат після remint.

Не розширювати Rust-контракт до `DomainIdentity`, не серіалізувати довільний Pair на хості, не змінювати очікування мовних законів. Новий CI має пройти physical producer → consumer, усі D9/F6 bindings/key laws і точні SHA квитанції. До цього `NATIVE_F6=NOT_VERIFIED`, `RELEASE=NO-GO`.

## Deutsch — Nachweisgrenze

Dieser Checkpoint startet CI nach dem kanonischen Remint. Die aktuelle F6-T5M-Paarung ist aktualisiert; der frühere `DomainIdentity`-Fehler stammt von einem älteren SHA. Keine Host-Serialisierung und keine Erweiterung des erlaubten Texttyps. Release bleibt NO-GO bis der native Producer-Consumer-Test auf demselben SHA besteht.

## English — release evidence boundary

This checkpoint ensures CI runs after the canonical remint. The current F6 T5M library pair has new blob hashes; the earlier `DomainIdentity` failure was observed on an older SHA. Do not coerce arbitrary SENS values to text or weaken the envelope contract. Release remains NO-GO until native producer→consumer passes on one exact SHA.

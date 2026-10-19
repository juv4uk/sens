; Визначальні константи Міжнародної системи одиниць SI.
; Джерело: BIPM, SI Brochure, дев'яте видання (2019).
;
; Єдине джерело кожного значення — структурований запис константи.
; Числові проєкції нижче читають ці записи, а не повторюють значення.
; Позначки scientific-constant/1, quantity/1, unit/1, dimension/1 і
; science-source/1 — поля усталеного формату наукових даних, а не
; викличні голови мови. Розмірності та походження даних зберігаються.
; Десяткові числа інтерпретує арифметика D24+; T5M відповідає
; виключно за фізичне пакування. Перехідних псевдонімів SID8/Sens8 немає.

; Форма запису:
; (scientific-constant/1 ІМ'Я (quantity/1 ЗНАЧЕННЯ ОДИНИЦЯ)
;   exact-by-definition physical-defining si
;   (science-source/1 bipm-si-brochure-9 2019))
(визначити сі:створити-запис-константи
  (функція (ім'я значення одиниця)
    (сполучити
      (як-є scientific-constant/1)
      (сполучити
        ім'я
        (сполучити
          (сполучити
            (як-є quantity/1)
            (сполучити
              значення
              (сполучити одиниця (як-є ()))))
          (як-є
            (exact-by-definition
              physical-defining
              si
              (science-source/1 bipm-si-brochure-9 2019))))))))

; Частота надтонкого переходу цезію-133, Гц.
(визначити si:defining-cesium-frequency
  (сі:створити-запис-константи
    (як-є si:cesium-frequency)
    9192631770
    (як-є (unit/1 (dimension/1 second -1)))))

; Швидкість світла у вакуумі, м/с.
(визначити si:defining-speed-of-light
  (сі:створити-запис-константи
    (як-є si:speed-of-light)
    299792458
    (як-є
      (unit/1
        (dimension/1 metre 1)
        (dimension/1 second -1)))))

; Стала Планка, Дж·с: точне раціональне значення.
(визначити si:defining-planck-constant
  (сі:створити-запис-константи
    (як-є si:planck-constant)
    (частка 132521403 200000000000000000000000000000000000000000)
    (як-є
      (unit/1
        (dimension/1 kilogram 1)
        (dimension/1 metre 2)
        (dimension/1 second -1)))))

; Елементарний електричний заряд, Кл.
(визначити si:defining-elementary-charge
  (сі:створити-запис-константи
    (як-є si:elementary-charge)
    (частка 801088317 5000000000000000000000000000)
    (як-є
      (unit/1
        (dimension/1 ampere 1)
        (dimension/1 second 1)))))

; Стала Больцмана, Дж/К.
(визначити si:defining-boltzmann-constant
  (сі:створити-запис-константи
    (як-є si:boltzmann-constant)
    (частка 1380649 100000000000000000000000000000)
    (як-є
      (unit/1
        (dimension/1 kilogram 1)
        (dimension/1 metre 2)
        (dimension/1 second -2)
        (dimension/1 kelvin -1)))))

; Стала Авогадро, моль⁻¹.
(визначити si:defining-avogadro-constant
  (сі:створити-запис-константи
    (як-є si:avogadro-constant)
    602214076000000000000000
    (як-є (unit/1 (dimension/1 mole -1)))))

; Світлова ефективність випромінювання частотою 540 ТГц, лм/Вт.
(визначити si:defining-luminous-efficacy
  (сі:створити-запис-константи
    (як-є si:luminous-efficacy)
    683
    (як-є
      (unit/1
        (dimension/1 candela 1)
        (dimension/1 kilogram -1)
        (dimension/1 metre -2)
        (dimension/1 second 3)))))

; Індексний закон: значення — друге поле вкладеної кількості,
; сама кількість — третє поле запису наукової константи.
(визначити сі:значення-константи
  (функція (наукова-константа)
    (друге (третє наукова-константа))))

; Числові поверхні для чинних споживачів. Вони не є копіями даних.
(визначити si:cesium-frequency (сі:значення-константи si:defining-cesium-frequency))
(визначити si:speed-of-light (сі:значення-константи si:defining-speed-of-light))
(визначити si:planck-constant (сі:значення-константи si:defining-planck-constant))
(визначити si:elementary-charge (сі:значення-константи si:defining-elementary-charge))
(визначити si:boltzmann-constant (сі:значення-константи si:defining-boltzmann-constant))
(визначити si:avogadro-constant (сі:значення-константи si:defining-avogadro-constant))
(визначити si:luminous-efficacy (сі:значення-константи si:defining-luminous-efficacy))

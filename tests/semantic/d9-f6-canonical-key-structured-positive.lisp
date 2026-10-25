; D9/F6: canonical key keeps a compound key as data and does not call atom-only identity.
(однакові?
  (фс-канонічний-ключ
    (список (як-є compound) (як-є key)))
  (список (як-є compound) (як-є key)))

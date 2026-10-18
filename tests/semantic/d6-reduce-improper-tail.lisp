; D6:101110 REDUCE must not accept improper nonempty tails as NIL.
(згорнути (функція (acc item) (сполучити item acc))
  (як-є ()) (сполучити (як-є а) (як-є обірвано)))

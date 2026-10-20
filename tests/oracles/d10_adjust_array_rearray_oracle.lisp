;;; Виконуване свідчення законів ADJUST-ARRAY у Common Lisp.
;;; Перевіряється у SBCL і не є оракулом історичної реалізації MacLisp.
(defun witness (назва умова)
  (unless умова (error "D10 ADJUST-ARRAY witness failed: ~A" назва))
  (format t "PASS ~A~%" назва))

;; Масив, розмір якого дозволено змінювати, зберігає свою тотожність.
(let* ((масив (make-array 2 :adjustable t :initial-contents '(alpha beta)))
       (результат (adjust-array масив 4 :initial-element :new)))
  (witness "adjustable-array-identity" (eq результат масив))
  (witness "in-bounds-elements-preserved"
           (and (eq (aref результат 0) 'alpha)
                (eq (aref результат 1) 'beta)))
  (witness "new-tail-initialized"
           (and (eq (aref результат 2) :new) (eq (aref результат 3) :new))))

;; Якщо повернуто інший масив, вихідний мусить залишитися незмінним.
(let* ((масив (make-array 3 :initial-contents '(alpha beta gamma)))
       (до-зміни (copy-seq масив))
       (результат (adjust-array масив 2)))
  (witness "adjust-result-dimensions" (= (array-total-size результат) 2))
  (witness "distinct-result-preserves-original"
           (or (eq результат масив) (equalp масив до-зміни))))

;; INITIAL-CONTENTS замінює вміст, а не зберігає попередні елементи.
(let* ((масив (make-array 2 :adjustable t :initial-contents '(old-a old-b)))
       (результат (adjust-array масив 2 :initial-contents '(new-a new-b))))
  (witness "initial-contents-replaces-old-data"
           (and (eq (aref результат 0) 'new-a) (eq (aref результат 1) 'new-b))))

;; FILL-POINTER T після зміни розміру відображає нову довжину вектора.
(let* ((вектор (make-array 2 :adjustable t :fill-pointer 1
                      :initial-contents '(alpha beta)))
       (результат (adjust-array вектор 4 :fill-pointer t :initial-element :extra)))
  (witness "fill-pointer-t-tracks-size"
           (and (eq результат вектор) (= (fill-pointer результат) 4))))

;; Зміщені масиви поділяють сховище й повідомляють основу та зсув.
(let* ((основа (make-array 6 :initial-contents '(0 1 2 3 4 5)))
       (джерело (make-array 2 :adjustable t :initial-contents '(8 9)))
       (результат (adjust-array джерело 3 :displaced-to основа
                             :displaced-index-offset 2)))
  (multiple-value-bind (підкладка зсув) (array-displacement результат)
    (witness "displacement-base-and-offset"
             (and (eq підкладка основа) (= зсув 2))))
  (setf (aref результат 0) 77)
  (witness "displacement-alias-visible" (= (aref основа 2) 77)))

;; Ланцюг зміщення зберігає посилання на безпосередній проміжний масив.
(let* ((основа (make-array 8 :initial-contents '(0 1 2 3 4 5 6 7)))
       (середній (make-array 5 :adjustable t :displaced-to основа
                      :displaced-index-offset 1))
       (зміщений (make-array 3 :displaced-to середній :displaced-index-offset 1)))
  (adjust-array середній 4 :initial-element 99)
  (multiple-value-bind (підкладка зсув) (array-displacement зміщений)
    (witness "chain-keeps-immediate-middle"
             (and (eq підкладка середній) (= зсув 1))))
  (setf (aref зміщений 0) 88)
  (witness "chain-mutates-adjusted-middle" (= (aref середній 1) 88)))

(format t "D10-ADJUST-ARRAY-SBCL-ORACLE: PASS~%")

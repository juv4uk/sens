;;; Д10: виконуване свідчення законів ADJUST-ARRAY у Common Lisp.
;;; Перевіряється у SBCL; це не оракул історичної реалізації MacLisp.
;;; Стандартні форми Common Lisp та контрольні мітки збережено.
;;; Авторські символи тестових даних, локальні змінні й коментарі — українською.

(defun засвідчити (назва умова)
  (unless умова
    (error "D10 ADJUST-ARRAY: свідчення не виконано: ~A" назва))
  (format t "PASS ~A~%" назва))

;; Масив, розмір якого дозволено змінювати, зберігає свою тотожність.
(let* ((масив (make-array 2 :adjustable t
                          :initial-contents '(альфа бета)))
       (результат (adjust-array масив 4 :initial-element :новий)))
  (засвідчити "adjustable-array-identity" (eq результат масив))
  (засвідчити "in-bounds-elements-preserved"
    (and (eq (aref результат 0) 'альфа)
         (eq (aref результат 1) 'бета)))
  (засвідчити "new-tail-initialized"
    (and (eq (aref результат 2) :новий)
         (eq (aref результат 3) :новий))))

;; Якщо повернуто інший масив, початковий має залишитися незмінним.
(let* ((масив (make-array 3 :initial-contents '(альфа бета гамма)))
       (до-зміни (copy-seq масив))
       (результат (adjust-array масив 2)))
  (засвідчити "adjust-result-dimensions"
    (= (array-total-size результат) 2))
  (засвідчити "distinct-result-preserves-original"
    (or (eq результат масив) (equalp масив до-зміни))))

;; INITIAL-CONTENTS замінює вміст, а не зберігає попередні елементи.
(let* ((масив (make-array 2 :adjustable t
                          :initial-contents '(старе-а старе-б)))
       (результат (adjust-array масив 2
                               :initial-contents '(нове-а нове-б))))
  (засвідчити "initial-contents-replaces-old-data"
    (and (eq (aref результат 0) 'нове-а)
         (eq (aref результат 1) 'нове-б))))

;; FILL-POINTER T після зміни розміру вказує на нову довжину вектора.
(let* ((вектор (make-array 2 :adjustable t :fill-pointer 1
                           :initial-contents '(альфа бета)))
       (результат (adjust-array вектор 4 :fill-pointer t
                               :initial-element :додатковий)))
  (засвідчити "fill-pointer-t-tracks-size"
    (and (eq результат вектор)
         (= (fill-pointer результат) 4))))

;; Зміщені масиви спільно використовують сховище й повідомляють зсув.
(let* ((основа (make-array 6 :initial-contents '(0 1 2 3 4 5)))
       (джерело (make-array 2 :adjustable t :initial-contents '(8 9)))
       (результат (adjust-array джерело 3 :displaced-to основа
                               :displaced-index-offset 2)))
  (multiple-value-bind (підкладка зсув) (array-displacement результат)
    (засвідчити "displacement-base-and-offset"
      (and (eq підкладка основа) (= зсув 2))))
  (setf (aref результат 0) 77)
  (засвідчити "displacement-alias-visible"
    (= (aref основа 2) 77)))

;; Ланцюг зміщення зберігає посилання на безпосередній проміжний масив.
(let* ((основа (make-array 8 :initial-contents '(0 1 2 3 4 5 6 7)))
       (середній (make-array 5 :adjustable t :displaced-to основа
                            :displaced-index-offset 1))
       (зміщений (make-array 3 :displaced-to середній
                            :displaced-index-offset 1)))
  (adjust-array середній 4 :initial-element 99)
  (multiple-value-bind (підкладка зсув) (array-displacement зміщений)
    (засвідчити "chain-keeps-immediate-middle"
      (and (eq підкладка середній) (= зсув 1))))
  (setf (aref зміщений 0) 88)
  (засвідчити "chain-mutates-adjusted-middle"
    (= (aref середній 1) 88)))

(format t "D10-ADJUST-ARRAY-SBCL-ORACLE: PASS~%")

; Explicit timezone data for WSM. Ukrainian projection only.
; Calendar semantics live in Lisp, not the host.

(визначити civil-from-days
  (функція (days)
    (нехай ((z (додати days 719468))
           (era (поділити z 146097))
           (doe (відняти z (помножити era 146097)))
           (yoe (поділити (відняти (додати doe (поділити doe 36524))
                              (додати (поділити doe 1460) (поділити doe 146096)))
                           365))
           (y (додати yoe (помножити era 400)))
           (doy (відняти doe (додати (помножити 365 yoe)
                           (відняти (поділити yoe 4) (поділити yoe 100)))))
           (mp (поділити (додати (помножити 5 doy) 2) 153))
           (day (додати (відняти doy (поділити (додати (помножити 153 mp) 2) 5)) 1))
           (month (додати mp
                    (за-умовою
                      ((менше? mp 10) 3)
                      ((атом? (як-є ())) -9))))
           (year (додати y
                   (за-умовою
                     ((більше? month 2) 1)
                     ((атом? (як-є ())) 0)))))
      (список year month day))))

(визначити utc-from-unix
  (функція (seconds nanosecond)
    (нехай ((days (поділити seconds 86400))
           (day-seconds (залишок seconds 86400))
           (civil (civil-from-days days))
           (hour (поділити day-seconds 3600))
           (minute (поділити (залишок day-seconds 3600) 60))
           (second (залишок day-seconds 60)))
      (список
        (сполучити (як-є year) (перше civil))
        (сполучити (як-є month) (друге civil))
        (сполучити (як-є day) (третє civil))
        (сполучити (як-є hour) hour)
        (сполучити (як-є minute) minute)
        (сполучити (як-є second) second)
        (сполучити (як-є nanosecond) nanosecond)))))

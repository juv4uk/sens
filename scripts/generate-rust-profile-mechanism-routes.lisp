; #1422 — породження механічної проєкції допуску механізмів Core×SENS.
;
; Джерело повноважень: lib/function-table-mechanisms.lisp (розділ profile-routes).
; Rust отримує тільки координати й вид маршруту. Закони, людські проєкції,
; синтаксис ядра, семантика результатів та окремі правила допуску лишаються в SENS.
;
; Запуск:
;   cargo run -p sens-cli -- scripts/generate-rust-profile-mechanism-routes.lisp
;   cargo run -p sens-cli -- scripts/generate-rust-profile-mechanism-routes.lisp --check

(визначити шлях-джерела "lib/function-table-mechanisms.lisp")
(визначити шлях-результату "crates/sens/src/eval/profile_mechanisms_generated.rs")

(визначити зчепити-рядки
  (функція аргументи
    (згорнути (функція (накопичувач частина) (рядок-додати накопичувач частина)) "" аргументи)))

(визначити метадані
  (перше (читати-всі (читати-файл шлях-джерела))))

(визначити знайти-розділ
  (функція (назва розділи)
    (за-умовою
      ((атом? розділи) () (як-є ()))
      ((атом? розділи) (0)
       (за-умовою
         ((тотожне? (перше (перше розділи)) назва) (1)
          (перше розділи))
         ((тотожне? (перше (перше розділи)) назва) (0)
          (знайти-розділ назва (решта розділи))))))))

(визначити рядки-профілів
  (решта (знайти-розділ (як-є profile-routes) метадані)))

(визначити профіль-раст
  (функція (профіль)
    (за-умовою
      ((тотожне? профіль (як-є core3))
       (1)
       "CoreProfile::Core3")
      (t (перше (як-є ()))))))

(визначити вид-маршруту-раст
  (функція (механізм)
    (за-умовою
      ((тотожне? механізм (як-є registered-host-mechanism))
       (1)
       "ProfileMechanismRouteKind::RegisteredHostMechanism")
      (t (перше (як-є ()))))))

(визначити подати-рядок
  (функція (рядок)
    (нехай-послідовно ((профіль (профіль-раст (перше рядок)))
           (ідентичність-сенс (друге рядок))
           (вид-маршруту (вид-маршруту-раст (третє рядок))))
      (за-умовою
        ((атом? профіль) () "")
        ((атом? вид-маршруту) () "")
        (t
         (зчепити-рядки
           "    ProfileMechanismRoute { profile: "
           профіль
           ", sens: crate::sens!("
           (значення-у-текст ідентичність-сенс)
           "), kind: "
           вид-маршруту
           " },\n"))))))

(визначити подати-рядки
  (функція (рядки)
    (за-умовою
      ((атом? рядки) () "")
      ((атом? рядки) (0)
       (зчепити-рядки (подати-рядок (перше рядки))
             (подати-рядки (решта рядки)))))))

(визначити заголовок
  (зчепити-рядки
    "// GENERATED — DO NOT EDIT BY HAND.\n"
    "// Authority: lib/function-table-mechanisms.lisp (profile-routes)\n"
    "// Generator: scripts/generate-rust-profile-mechanism-routes.lisp\n\n"
    "use crate::{CoreProfile, CoreDomainIdentity};\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "#[allow(dead_code)]\n"
    "pub(crate) enum ProfileMechanismRouteKind {\n"
    "    RegisteredHostMechanism,\n"
    "}\n\n"
    "#[derive(Clone, Copy, Debug, Eq, PartialEq)]\n"
    "struct ProfileMechanismRoute {\n"
    "    profile: CoreProfile,\n"
    "    sens: CoreDomainIdentity,\n"
    "    kind: ProfileMechanismRouteKind,\n"
    "}\n\n"
    "const PROFILE_MECHANISM_ROUTES: &[ProfileMechanismRoute] = &[\n"))

(визначити закінчення
  (зчепити-рядки
    "];\n\n"
    "pub(crate) fn profile_mechanism_route(\n"
    "    profile: CoreProfile,\n"
    "    sens: CoreDomainIdentity,\n"
    ") -> Option<ProfileMechanismRouteKind> {\n"
    "    PROFILE_MECHANISM_ROUTES\n"
    "        .iter()\n"
    "        .find(|row| row.profile == profile && row.sens == sens)\n"
    "        .map(|row| row.kind)\n"
    "}\n"))

(визначити згенерований-вміст
  (зчепити-рядки заголовок (подати-рядки рядки-профілів) закінчення))

(за-умовою
  ((атом? *argv*)
   ()
   (друге
     (список
       (записати-файл шлях-результату згенерований-вміст)
       (друкувати "Rust profile mechanism projection written"))))
  ((однакові? (перше *argv*) "--check")
   (1)
   (нехай ((чинний-вміст (читати-файл шлях-результату)))
     (за-умовою
       ((однакові? чинний-вміст згенерований-вміст)
        (1)
        (друкувати "Rust profile mechanism projection is current"))
       ((однакові? чинний-вміст згенерований-вміст)
        (0)
        (друге
          (список
            (друкувати "Rust profile mechanism projection is stale")
            (перше (як-є ()))))))))
  ((як-є write-projection)
   write-projection
   (друге
     (список
       (записати-файл шлях-результату згенерований-вміст)
       (друкувати "Rust profile mechanism projection written")))))

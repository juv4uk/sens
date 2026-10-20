; Історичні/точкові свідчення семантичного огляду.
; Від #1347 цей файл НЕ є списком дозволів для семантики Rust/хоста, і
; scripts/semantic-authority-guard.lisp більше його не споживає.
;
; Деякі точкові робочі процеси (наприклад, свідчення Core2) досі вживають точні
; рядки path+SHA як свідчення відтворюваності. Ці рядки не надають і не
; відбирають семантичної влади.
;
; #1098 SID-BINARY-IDENTITY-1 — оглянута міграція подання:
; семантична ідентичність змінюється з числових псевдонімів хоста на непрозорий точний 8-бітовий Sid8.

(review "crates/my-lisp/src/eval/builtins.rs" "4ca9b106abd671eccc1abd0c8c9401d219b898c6df72801ab67cb1dea9a0b4f1" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/eval/canon.rs" "fe6778da084a92806e7a589592aae13bf250876bba429ea2dd0e8f00a4c5409c" issue-1292 sid-primary-index-over-canon-identity)
(review "crates/my-lisp/src/eval/mod.rs" "b82488395827e94ef910ca554962bc9008811d8cae4121dbe6d3533849d7293e" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/eval/necessary_forms.rs" "6876d0aeec8b7d26b0014a51e194af8cd68ce3bcc84ecaffd974ce27557b55f5" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/ir.rs" "619143298b56b4788c4c2de1c84023e1cc19449dea8729bdf4e9ccbb07128410" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/language_items.rs" "f772ebce9c52525c355f944a7472986a70034ae30a70537878444766c02b9f69" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/lib.rs" "d8cf1aff9c382c98ddae1b8e5e1087135403d91441d1d16c21b32e2e9f570fe4" issue-1098 sid8-projection-boundary)
(review "crates/my-lisp/src/presentation.rs" "436b74f73df5a1c00ee4a35b32ec01aab0441f0fda717ede346bdca3cbdae288" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/semantic_registry.rs" "9677f513b2fe3ad319f1f371f30c2d4649c4969839de5da852f488426083aec3" issue-1098 sid8-projection-boundary)
(review "crates/my-lisp/src/value.rs" "96d89de14c18dec59101bbcda60ff9f9abbafb9b9e6b2271cea3f318dbaa6179" issue-1098 sid8-type-migration)
(review "crates/my-lisp/tests/machine_capability_axis.rs" "f9c7e69325cc02bcdb4646acd4fa1a15aa49ba0edf52477e529cfdd870e0268e" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/rivnopravnist_mov.rs" "5280e7f47de4ee4bf4d10731e1b0d05a4e2bda78fc6fbc8176596e6a646b05da" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/semantic_coordinate_join.rs" "102a70d74902b90d029a96e1f0d02c81dbd4e7f7afff2298bab303f10e39beba" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/semantic_coordinate_join_2.rs" "49328492430e58e516ce926d77808a111992fdd586356c517c462db7c222baeb" issue-1098 sid8-witness-migration)
(review "crates/xtask/src/external_oracle.rs" "9ad5faa5003a3e440ffc1408f4f4e7f4d3985508c34933d0425e796bab4e7f05" issue-1098 sid8-tooling-migration)
(review "crates/my-lisp/tests/uk_surface_equivalence.rs" "a726233e46be11fdfaabcb8b84074cfcba8beb919b753334411c2b092a2c1a63" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/rivnopravnist_mov.rs" "40cfe6b0dd9808a31be1f161a5da05982a1b7b15f6b3a5ac5dea063062ae5112" issue-1098 legacy-export-sid8-boundary-witness)

; #1101 SID-RUNTIME-UNIFY-1 вилучає дубльований runtime-рід SemanticRef.
(review "crates/my-lisp/src/eval/mod.rs" "01c8053accb96d1c91e49073ecf59681df8fe5c86eef7c97b0eddea49a361465" issue-1101 single-sid-runtime)
(review "crates/my-lisp/tests/clock.rs" "035fd471b3b9a1f30fb77d8d92eb84986f2461d9899d7a7b1ffff7ea9ce9d9e2" issue-1101 sid-witness-migration)
(review "crates/my-lisp/tests/timezone_ownership.rs" "72ad98691141e7dbdf496bd300ecb5a3dc26aed7e580a5021643ed256663aa23" issue-1101 sid-witness-migration)
(review "crates/my-lisp/src/presentation.rs" "235c7ff4d8c76fb72c0eaaf5663bf690395f6216c52d625d73f6dc86a521c510" issue-1101 single-sid-presentation-projection)

; #992 спостереження рідного результату CLIPS: оглянутий механізм-лише адаптер.
(review "crates/wsm-clips-kernel/src/lib.rs" "2ea4eb418c1ac76820145236773caa212a72e39f3d27211bf5608278437a5a0e" issue-992 clips-result-observation-mechanism)
(review "crates/wsm-clips-kernel/tests/c_abi_semantic_witness.rs" "9498c9ab5018b9d0270c72d3906d2f202053a489f4ac4128c3859c2cd33019f0" issue-992 clips-result-observation-witness)

; #1169 межа CLIPS SID8: оглянуте вилучення текстової семантичної диспетчеризації операторів.
; Хостовий код лише вилучає текстовий шлях виконання; він не відображає рідні
; оператори/назви на SID. Сирий Eval лишається лише діагностичним поза семантичним обміном.
(review "crates/wsm-clips-kernel/src/lib.rs" "e240e4402db8ec44859e1055ccf2cb3e30757517344fa7ea611beeb1c8e34b56" issue-1169 clips-text-dispatch-removal-mechanism)
(review "crates/wsm-clips-kernel/tests/c_abi_semantic_witness.rs" "b701171e34685d0aa9753d836052d5bc2c2c5c33a238852f36570e4d9f602104" issue-1169 clips-text-dispatch-removal-witness)

; #1133 профіль виконання Core2: оглянутий механізм вибору профілю та свідок-спостерігач.
(review "crates/my-lisp/src/environment.rs" "9477dfa4f673a1e490d13d7d9512c919ddbfb18f65028402e0af14702037460d" issue-1133 core2-session-cond-mode)
(review "crates/my-lisp/src/eval/special_forms/core.rs" "96c35aaae7bb11c53138bbc080590c86daad2ea3fe4ae2555106e0b356ef8024" issue-1133 core2-cond-dispatch-mechanism)
(review "crates/my-lisp/src/lib.rs" "a4a37a9e086222440ac438b6c20590f573337037c1063e638b57c1ef0a9b5651" issue-1133 core2-loader-mechanism)

; #1173 міграція поля ідентичності SID8: оглянуті оновлення тестів лише-спостерігачів.
(review "crates/my-lisp/tests/witness_authority.rs" "bc5d4b359a169a5edc1cf3e2d0fb90e3bd7daa87e2d7e4d335ab467f9c76d492" issue-1173 sid8-identity-field-observer)
(review "crates/my-lisp/tests/semantic_coordinate_join.rs" "02cf206794a877fa894b8baf21c2b3a7ff8d97908b8896648005de30b69586a8" issue-1173 sid8-identity-field-observer)
(review "crates/my-lisp/tests/semantic_coordinate_join_2.rs" "ff0709c7ddf2dcd31be16e6ecf2572d154a51e36512f86910ee5338c09276aeb" issue-1173 sid8-identity-field-observer)
(review "crates/my-lisp/tests/semantic_coordinate_matrix_845.rs" "510f3c0ede3407dbc502815db845efdb1a90f7e4e5d5259123851c0d5cd03541" issue-1173 sid8-identity-field-observer)
;
; #1001 арифметика Datalog direct-SID8: оглянуте відображення хоста лише-механізму.
; Точний SID8 обирає обмежену рідну цілочисельну машинерію; корисне навантаження несе
; лише аргументи. Ці хостові файли можуть виконувати вже власний SID, але не можуть
; карбувати чи перетлумачувати семантичну ідентичність.
(review "crates/wsm-datalog-kernel/src/arithmetic.rs" "79f10471d3b80f988496bb41b1a406a5b20788d386bfa710d0918eebbba8fbf2" issue-1001 datalog-direct-sid8-arithmetic-mechanism)
(review "crates/wsm-datalog-kernel/src/lib.rs" "e5c29f665637b802df1b1f8eb7283ab21ce5b0690690e831c7d4afa1ee2acabd" issue-1001 datalog-direct-sid8-abi-mechanism)
(review "crates/wsm-datalog-kernel/tests/arithmetic_execution_1001.rs" "91bbd2992e344bcae083d38edd96de30fa0b523c4376c8a430c1fc2f661d93ca" issue-1001 datalog-direct-sid8-observer)

; #1217 Common Lisp + семантичний ABI: оглянуте прив'язування точного SID8 механізму.
; Сирий CommonLispKernel::evaluate лишається діагностичним/рідним; спільний семантичний
; ABI прив'язує SID 00001100 до обмеженого додавання і приймає лише аргументи.
(review "crates/wsm-common-lisp-kernel/src/lib.rs" "d1c04c59757776a059981110a6622a1923ecf9b0be70b784448a3407f4e6f6f0" issue-1217 common-lisp-direct-sid8-add-mechanism)
;
; #1218 Prolog + семантичний ABI: оглянуте прив'язування точного SID8 механізму.
; Сирі/рідні API запитів Prolog лишаються доступними; спільний семантичний обмін прив'язує
; SID 00001100 до обмеженого додавання і приймає лише аргументи.
(review "crates/wsm-prolog-kernel/src/lib.rs" "dc79cdbfd2544671cc3aace6ba0b1dac5ae0dc0632b41a7370f8aafe137cd2b6" issue-1218 prolog-direct-sid8-add-mechanism)
(review "crates/wsm-prolog-kernel/tests/c_abi_semantic_witness.rs" "58e811d00961470f7f1d7ff5591aa5eeadc339f9dd0ef5a1d26727661350a245" issue-1218 prolog-direct-sid8-observer)
;
; #1169 CLIPS + семантичний ABI: оглянуте прив'язування точного SID8 механізму.
; Сирий ClipsEnvironment::eval_bytes лишається діагностичним/рідним. Спільний семантичний
; обмін прив'язує SID 00001100 до обмеженого додавання і приймає лише аргументи.
(review "crates/wsm-clips-kernel/src/lib.rs" "c32f92feca2eec1a762a9e73143ad9fc7e8bd07886d5c1a3b2bcdae9e19c7866" issue-1169 clips-direct-sid8-add-mechanism)
(review "crates/wsm-clips-kernel/tests/c_abi_semantic_witness.rs" "dfcb1b5ec8458c750d2e55b5fd9bdbc3d1601939e6644727f18db68a258a36cf" issue-1169 clips-direct-sid8-observer)

; #1173 вісь машинних можливостей: оглянута міграція SID8 лише-спостерігача.
(review "crates/my-lisp/tests/machine_capability_axis.rs" "bddbb702a652f3bee692bde36d1d3a3d8253d82a4836fd1900e95a6719efc091" issue-1173 sid8-machine-capability-observer)
(review "crates/my-lisp/tests/semantic_coordinate_join.rs" "2fcfb8d8a2f0d624d37edc85744c456d614b862c54094792939302cf9914509c" issue-1173 sid8-machine-capability-observer)
(review "crates/my-lisp/tests/semantic_coordinate_join_2.rs" "11ea19e3132fb4dcc57ce6f9eadc689afda1665c39b43ed4bccadab0fe9bbc92" issue-1173 sid8-machine-capability-observer)

; #1173 закон/матриця семантичних координат: оглянута міграція SID8 лише-спостерігача.
(review "crates/my-lisp/tests/semantic_coordinate_join.rs" "e4fcb7565113c9ef00625291407e58c859147a642ee0b9318e0a0eb5ad93fa06" issue-1173 sid8-coordinate-law-observer)
(review "crates/my-lisp/tests/semantic_coordinate_join_2.rs" "b86a8cafd47ab28485fead3b286d1f7538301fc4a85c6448ff978e415e10a1b1" issue-1173 sid8-coordinate-law-observer)
(review "crates/my-lisp/tests/semantic_coordinate_matrix_845.rs" "40e887899288624ffb1ffd9d2d105792bc13f8edeed974b142b83a2a38035380" issue-1173 sid8-coordinate-law-observer)

; #1173 міграція поля ідентичності structure-core: спостерігач вимагає точний Sid8.
(review "crates/my-lisp/tests/witness_authority.rs" "1fc6670a70d5392b7a2188133c8b911781614bb1dff763cff552281d3669d43c" issue-1173 structure-core-sid8-observer)

; #1294 лише спостерігач: порівняти членство канонічних визначень Core4 з публічним/внутрішнім інвентарем, що належить Lisp.
(review "crates/my-lisp/tests/uk_surface_inventory.rs" "eb1973408cfd59ecccc9dd746b24da72361a6892c8aade40f17a8d6b1998d031" issue-1294 canonical-core4-definition-observer)
; тести ранжування evidence-status для guard-reference: хост перевіряє, що синтетичні (reference ...)
; записи виграють за evidence-status через guard-reference-find/-all; Lisp (knowledge/guard-reference.lisp)
; володіє законом ранжування, цей файл лише спостерігає його вивід.
(review "crates/my-lisp/tests/guard.rs" "8c56e37f5ea4044e8f1afe6db57e437fde00bfed7a0304fc4509500b17f2a2b5" issue-guard-evidence-ranking guard-reference-evidence-status-observer)
; #1312 спостерігач world.rs: тестує переходи світу, знімки та адреси вмісту,
; спостерігаючи контракти, що належать Lisp: contracts/world-transition-contract.lisp.
(review "crates/my-lisp/tests/world.rs" "bcddce8a78c6182fadb92528e7bf8f3889e0ec4c3ee295ef56ae1cb8c0b3efe3" issue-1312 world-transition-observer)

; #1325 перехід лише-SID8: наявний механізм eval стає прямо викликним наявним SID 01001101.
; Жодного нового значення функції в Rust не створюється; це вилучає з bootstrap шлях виконання лише-за-назвою.
(review "crates/my-lisp/src/eval/canon.rs" "8e6e9239bdb42c203d315282a2200e364a586092c0ff717bdeb51a495a299769" issue-1325 sid8-01001101-existing-mechanism)

; #1332 міграція Контракту-9: порожня структура — не функція SID 00000000.
; Rust вилучає історичне зв'язування EmptyList<->SID0; жодного нового значення функції не карбується.
(review "crates/my-lisp/src/eval/canon.rs" "98ea7a845a4ba6335a84021929f340581192d3416eb1a3c780c16386ed2c9304" issue-1332 sid0-empty-list-decoupling)
(review "crates/my-lisp/src/eval/mod.rs" "172b273f58cd65e63a2d81e549ea4838de227b559059dc05bb7e4dc33ddba706" issue-1332 empty-structure-direct-value)
(review "crates/my-lisp/src/ir.rs" "92102163b52f71fe37d9e5f4ae6b48fec4525ed674ea334918249a723f9a23dc" issue-1332 empty-structure-ir-outside-sid-space)

; #1327 прибирання Контракту-9: вилучити іменовану CanonicalIdentity; ідентичність функції лишається лише Sid8.
(review "crates/my-lisp/src/eval/canon.rs" "11435b6091c0e1c13d2e842cc4e634cbc684ec749547c4e45ea437c85def446c" issue-1327 sid8-only-mechanism-routing)
(review "crates/my-lisp/src/eval/mod.rs" "86a1ec5f2d052e8b4ba3422485cdb701962d902be55e76045966bcb2290e04f7" issue-1327 sid8-only-special-route-selection)
(review "crates/my-lisp/src/lib.rs" "edc4948041a9574cb233faad8a7a5829c7533fded9a438e37c27e77f065217d2" issue-1327 generic-surface-to-sid-routing)
(review "crates/my-lisp/src/ir.rs" "72ad065142bf0b94f8d1dc1cdcdfcca32b698879d6a5333dd145529eba9bcc9f" issue-1327 sid8-only-ir-provenance)
; #1344 основа словника Sens: експортує Sens8, Sens, sens! поряд із Sid8.
(review "crates/my-lisp/src/lib.rs" "340674a9c5bd7cbd6ef5b6716955bfb28e9ddd3da6ce42fd0486110954ae4370" issue-1344 sens-vocabulary-foundation-export)
(review "crates/my-lisp/tests/sens_foundation.rs" "3fbba9fff5cd2e04581fa45e31d1141ebcb15804650f56e70aaf24e7525e8d35" issue-1344 sens-foundation-observer)
(review "crates/my-lisp/src/presentation.rs" "7f1815c6adeea63e2246f1d5a9fe9eb7f58660ac6c399f440f1139a68762b68b" issue-1327 sid8-diagnostic-observer-alignment)
; #1368 вирівнювання 256 ідентичностей Sens у тестах-спостерігачах.
(review "crates/my-lisp/tests/rivnopravnist_mov.rs" "d20b06306ff4089fd2e5174304bc2464d5b6b883d0ad4eab995dde8deed10a8e" issue-1368 sens-256-identities-observer)
(review "crates/my-lisp/tests/semantic_registry_lisp.rs" "0c6df2ec3c679d2cb9bb55b54e47231757dc7b5285c313f8c8f1c0d459f17569" issue-1368 sens-256-identities-observer)

; #1272 транспорт вибраного Core: завантажувач встановлює лише механічний сигнал профілю; законами володіють контракти Lisp.
(review "crates/my-lisp/src/lib.rs" "464bfce89601a1fb3146d8d7b4b748f34192f00971700b2060a8947d151a113a" issue-1272 selected-core-profile-mechanical-loader)

; #1006 основа SENS-first raw invoke: оглянутий хостовий шов лише-механізму.
(review "crates/my-lisp/src/eval/capabilities.rs" "657d49756897d6c8ec6a9ef7f644822f491eb504bc13a78d5b9f2f3c1e9cec16" issue-1006 exact-sens-host-mechanism-registry)
(review "crates/my-lisp/src/eval/canon.rs" "ec4ee0f848166f5ea5891204f3f09e9bc37112cc82e25017bc7051d6a71f3ac3" issue-1006 sens-mechanism-fallback-after-local-function)
(review "crates/my-lisp/src/eval/mod.rs" "3730c906dc384b9bd6bc56fe215202251d846db68d3a5cadc1e9ef8058a25b8f" issue-1006 sens-mechanism-api-export)
(review "crates/my-lisp/src/lib.rs" "c6fb80f302fb0e138f2515cf9e5ba433a23f4bdda968aafc19d4cd043b59cb2e" issue-1006 sens-mechanism-public-export)
; #1406: загальна хостова доступність не має ставати звичайним допуском SENS.
(review "crates/my-lisp/src/eval/canon.rs" "0fc923c893012610a6aad60edbdcaf70e9a78b67b7b63fbba6eb18d0c512fece" issue-1406 registration-is-not-admission-repair)
(review "crates/my-lisp/tests/sens_host_registration_admission_1406.rs" "729d3a741df2b4f2fd7cb278b09107e449c6b19eaf58241a5e5b25bdd58cf248" issue-1406 sens-host-registration-admission-observer)
(review "crates/my-lisp/src/eval/capabilities.rs" "263e6fcfeb94974a8a6d102df296ee25d6fa23888015cd73b6d3654d14062347" issue-1406 dormant-host-registry-mechanism)
(review "crates/my-lisp/src/lib.rs" "f898bce28b2fec3210c71fb2e230ea3041c18f4f9f499618abf09b01c66f8b68" issue-1414 explicit-core3-profile-loader-mechanism)

; #1432 англійські предикати зі знаком питання: вирівняти твердження тестів.
(review "crates/my-lisp/src/eval/mod.rs" "8d0352de416852cf928520f4f16b8d11c6882c7f16aae74107ede48db19f35a6" issue-1432 english-predicate-question-mark-test)
(review "crates/my-lisp/src/presentation.rs" "ebb12056da482bf59ee37645eda8ca60c22cf9f0a7819f115952262bcb55e53e" issue-1432 english-predicate-question-mark-test)

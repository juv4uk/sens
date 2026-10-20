; Область відповідальності репозиторію SENS за контрактом координації 0.1.
; Повний опис: docs/swarm-mesh-v2.md. Формат перевірено порівнянням
; з історичними прикладами fpga-lisp/repo.my, shiva-sutras/repo.my
; і tauricode/repo.my (MYLISP-SWARM-CONTRACT-01).
;
; Це оголошення меж відповідальності, а не надання дозволів.
; Поля authorities і non-authorities є назвами чинного протоколу:
; вони вказують, для чого цей репозиторій є джерелом істини,
; щоб інші агенти не встановлювали ці межі заново.

(repository
  (id my-lisp)
  (role language-core)
  (exports language-contract conformance-fixtures core-libs
    semantic-oracle machine-lowering-boundary machine-effect-boundary semantic-effect-lowering swarm-node)
  (imports swarm-contract)
  (capabilities lisp rust testing docs debugging swarm-coordination)
  (authorities language-semantics runtime-core standard-library
    swarm-protocol-implementation)
  (non-authorities cml-compilation fpga-hardware sanskrit-canon
    paninian-ontology agent-workstation-ui registry-data))

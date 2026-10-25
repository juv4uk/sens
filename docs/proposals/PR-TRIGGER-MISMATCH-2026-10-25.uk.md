# РОЗБІЖНІСТЬ ТРИГЕРІВ: 25 workflow обробляють PR-події, але тригера не мають

Автор: агент Sañcāra, 2026-10-25.

## Що знайдено

**25 workflow читають `github.event.pull_request`**, тобто **написані для роботи на
pull request**, — але їхній тригер — лише `workflow_dispatch`. Тобто код обробляє
PR-подію, якої **ніколи не буває**.

Найяскравіший приклад — `audit-t5-file-pairs.yml`:
- рядок 43: `BASE_SHA: ${{ github.event_name == 'pull_request' && github.event.pull_request.base.sha || github.event.before }}`
- рядок 97: `# No source modification, no git push, no automatic semantic admission.`
- `permissions: contents: read`, job `read-only-audit`

**Він створений для PR, безпечний (лише читання), і саме він перевіряє ПАРИ — але
не запускався ніколи.**

## Що я виправив

`audit-t5-file-pairs.yml` — додано тригер:
```yaml
on:
  pull_request:
    branches: [main]
  workflow_dispatch:
```
Перевірено: `CHECK_WORKFLOW_YAML_PASS: 531 воркфлоу парсяться`.

## Що лишилось — повний список

БЕЗПЕЧНІ (лише читання, без push) — перевести на pull_request:
  - audit-t5-program-syntax.yml
  - binary-only-authority.yml
  - canon-content-store-witness.yml
  - ci-heavy.yml
  - d10-class-of-proposal.yml
  - gpu-exact-domain-2046.yml
  - historical-setq-research.yml
  - important-file-guard.yml
  - measurement-triad.yml
  - post-d4-evalquote.yml
  - post-d4-label-lower-bound.yml
  - post-d4-pairlis-derivation.yml
  - verify-524-d295-cli.yml

ПОТРЕБУЮТЬ ОГЛЯДУ (пишуть або push):
  - compiler-role-cutover.yml
  - current-exact-domain-corpus.yml
  - d1-d8-runtime-cutover.yml
  - domain-mechanism-bench.yml
  - exact-width-admitted-corpus.yml
  - foundation-compatibility-bench.yml
  - generation-accounting.yml
  - generation-certificate.yml
  - issue-74-real-readfile-benchmark.yml
  - release-preflight.yml
  - sens-code-migration.yml

## Deutsch

25 Workflows verarbeiten PR-Ereignisse, haben aber keinen Auslöser.

## English

25 workflows handle PR events but have no trigger.

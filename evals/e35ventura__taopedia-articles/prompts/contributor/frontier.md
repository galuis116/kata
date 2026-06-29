# PromptForge Contributor Prompt: Taopedia Articles

Repo: `taopedia-articles`
GitHub: `e35ventura/taopedia-articles`

This prompt is source-grounded from repo files and the configured SN74 registry.

## Repo Overview
- This repository contains the public MDX article source for Taopedia, a Bittensor-focused knowledge base. (repo:README.md)

## Contribution Rules
- Use the required front matter. (repo:CONTRIBUTING.md)
- category: One primary topic. Do not use Bittensor as a catch-all category. (repo:CONTRIBUTING.md)
- tags: Zero to three specific topic tags. Do not use Bittensor; every published Taopedia article is already Bittensor-focused. (repo:CONTRIBUTING.md)
- Keep sentences direct; do not use a long explanation when a short one preserves the meaning. (repo:CONTRIBUTING.md)
- Sources are required for factual and technical claims. AI-assisted writing is allowed, but unsourced writing is not. (repo:CONTRIBUTING.md)
- Do not use generic homepages, SEO pages, social posts, or screenshots as support for technical claims unless they are clearly marked as context and no stronger source exists. (repo:CONTRIBUTING.md)
- Every section should add a new fact, distinction, caveat, source, or operational detail. (repo:CONTRIBUTING.md)
- When docs and code disagree, code is the source of truth for implementation behavior. Docs can support conceptual explanations, but exact mechanics should be backed by code, release notes, or official specs. (repo:CONTRIBUTING.md)

## Validation Commands
- `npm run format:check` (repo:CONTRIBUTING.md)
- `npm run validate` (repo:CONTRIBUTING.md)

## Protected Paths
- Repository-wide ownership rules exist (`*`). (repo:.github/CODEOWNERS)

## PromptForge PR Checklist
- Run the most relevant validation commands above before opening the PR. (repo:CONTRIBUTING.md)
- Avoid changing protected or maintainer-owned paths unless explicitly intended. (repo:.github/CODEOWNERS)
- Include the required visual evidence for visible UI changes. (repo:CONTRIBUTING.md)

## Scoring / Registry Notes
- Registry entry found for `e35ventura/taopedia-articles`. (https://raw.githubusercontent.com/entrius/gittensor/test/gittensor/validator/weights/master_repositories.json)
- `emission_share`: `0.025` (https://raw.githubusercontent.com/entrius/gittensor/test/gittensor/validator/weights/master_repositories.json)
- `trusted_label_pipeline`: `True` (https://raw.githubusercontent.com/entrius/gittensor/test/gittensor/validator/weights/master_repositories.json)
- `label_multipliers`: article=1.0, correction=1.25, image=0.75, category=0.5, other=0.1 (https://raw.githubusercontent.com/entrius/gittensor/test/gittensor/validator/weights/master_repositories.json)
- `eligibility`: min_credibility=0.5, min_token_score_for_valid_issue=0.0 (https://raw.githubusercontent.com/entrius/gittensor/test/gittensor/validator/weights/master_repositories.json)

## Unknowns / Caveats
- No major source gaps were detected in the current scan.

## Sources
- https://github.com/e35ventura/taopedia-articles.git
- repo:README.md
- repo:CONTRIBUTING.md
- repo:.github/CODEOWNERS
- repo:.github/workflows/build-index.yml
- repo:.github/workflows/pr-source-check.yml
- repo:.github/workflows/release.yml
- repo:.github/workflows/trigger-taopedia-deploy.yml
- repo:.github/workflows/validate-content.yml
- https://raw.githubusercontent.com/entrius/gittensor/test/gittensor/validator/weights/master_repositories.json

# PromptForge

PromptForge is an objective prompt optimization repo for SN74/Gittensor.

It generates repo-specific prompts, evaluates them against pinned repo tasks, compares them with
baseline prompts, and reports whether they improve verified task success.

Current MVP scope:

- generate one source-grounded repo-specific prompt
- compare it with a fixed generic baseline
- store a current frontier prompt per repo and mode
- challenge that frontier with a candidate prompt on primary and holdout task pools
- score prompts on pinned repo tasks with objective checks

The current repo is an objective optimization harness first. It now supports a baseline/frontier/
challenger workflow for prompt competition, but it is not yet a full multi-candidate prompt-search
system.

PromptForge is not a prompt library. The core claim is:

> a generated prompt is only better if it solves more validated repo tasks under the same eval
> conditions.

## Measurement Model

Prompt quality is measured with controlled repo evals:

- same repo snapshot
- same task
- same agent command
- same model and budget
- baseline prompt vs PromptForge-generated prompt

Each task defines objective checks in `checks.sh`. A prompt only improves if it increases verified
task success, not because the wording looks better.

## Registration MVP Interfaces

```bash
promptforge generate --repo <repo-path> --mode contributor
promptforge baseline --repo <repo-path>
promptforge eval --repo <repo-path> --eval-pack evals/<repo-name> --agent-command '<command>'
promptforge frontier init --repo <repo-path> --eval-pack evals/<repo-name> --mode contributor
promptforge challenge --eval-pack evals/<repo-name> --mode contributor --candidate-prompt <path> --agent-command '<command>'
promptforge frontier promote --challenge-run <challenge-summary.json>
promptforge report --run <run-id>
```

## Current Benchmark Pack

The first real eval pack is for:

- `e35ventura/taopedia-articles`

It currently includes three pinned contributor tasks:

- `add-delayed-proxies-article`
- `clarify-subnet-77-identity-mapping`
- `clarify-validator-take-vs-stake-weight`

Each task:

- pins the repo commit in `repo_ref.txt`
- limits allowed edit paths
- defines task-specific pass/fail checks
- can be executed through the standard `promptforge eval` flow

The repo now also includes a contributor frontier manifest for this pack:

- `evals/e35ventura__taopedia-articles/frontier.json`

It defines:

- a fixed baseline prompt
- the current frontier prompt
- a primary task pool
- a holdout task pool used for retest before promotion

## Competition Workflow

PromptForge now supports a miner-facing baseline/frontier/challenger loop:

1. `baseline`
   A fixed generic prompt used as the control.
2. `frontier`
   The current best verified prompt for a repo and mode.
3. `challenger`
   A new candidate prompt trying to replace the frontier.

Competition flow:

1. initialize the frontier manifest for a repo and mode
2. evaluate `baseline`, `frontier`, and `challenger` on the same primary task pool
3. if the challenger beats the frontier, retest on the holdout task pool
4. only promote the challenger if it beats the frontier on both pools

The baseline is not the production prompt miners use. It is the fixed control used to measure
whether repo-specific optimization is adding value at all.

## Local Workflow

Generate a repo-specific prompt:

```bash
uv run python -m promptforge generate \
  --repo https://github.com/e35ventura/taopedia-articles.git \
  --mode contributor
```

Validate the task pack:

```bash
uv run python -m promptforge eval-pack validate \
  --path evals/e35ventura__taopedia-articles
```

Run an eval:

```bash
uv run python -m promptforge eval \
  --repo https://github.com/e35ventura/taopedia-articles.git \
  --eval-pack evals/e35ventura__taopedia-articles \
  --mode contributor \
  --agent-command '<your-agent-command>'
```

Render a report:

```bash
uv run python -m promptforge report --run <run-id>
```

Initialize a frontier manifest and prompt artifacts:

```bash
uv run python -m promptforge frontier init \
  --repo https://github.com/e35ventura/taopedia-articles.git \
  --eval-pack evals/e35ventura__taopedia-articles \
  --mode contributor \
  --primary-task add-delayed-proxies-article \
  --primary-task clarify-validator-take-vs-stake-weight \
  --holdout-task clarify-subnet-77-identity-mapping
```

Inspect the current frontier:

```bash
uv run python -m promptforge frontier show \
  --eval-pack evals/e35ventura__taopedia-articles \
  --mode contributor
```

Challenge the frontier with a candidate prompt:

```bash
uv run python -m promptforge challenge \
  --eval-pack evals/e35ventura__taopedia-articles \
  --mode contributor \
  --candidate-prompt path/to/candidate.md \
  --agent-command "$PWD/scripts/run_codex_eval.sh"
```

Promote a winning challenger into the frontier:

```bash
uv run python -m promptforge frontier promote \
  --challenge-run runs/<challenge-run>/challenge_summary.json
```

## Real Agent Commands

PromptForge evals are designed to call a real agent command. This repo now includes two adapter
scripts:

- `scripts/run_codex_eval.sh`
- `scripts/run_claude_eval.sh`

Example with Codex:

```bash
uv run python -m promptforge eval \
  --repo https://github.com/e35ventura/taopedia-articles.git \
  --eval-pack evals/e35ventura__taopedia-articles \
  --mode contributor \
  --agent-command "$PWD/scripts/run_codex_eval.sh"
```

Example with Claude:

```bash
uv run python -m promptforge eval \
  --repo https://github.com/e35ventura/taopedia-articles.git \
  --eval-pack evals/e35ventura__taopedia-articles \
  --mode contributor \
  --agent-command "$PWD/scripts/run_claude_eval.sh"
```

Optional model overrides:

```bash
PROMPTFORGE_CODEX_MODEL=o3 \
uv run python -m promptforge eval ... --agent-command "$PWD/scripts/run_codex_eval.sh"

PROMPTFORGE_CLAUDE_MODEL=sonnet \
uv run python -m promptforge eval ... --agent-command "$PWD/scripts/run_claude_eval.sh"
```

These adapters assume the corresponding CLI is already authenticated and available on `PATH`.

## Current Status

The core CLI path is working:

- prompt generation
- baseline generation
- eval-pack scaffolding and validation
- eval execution
- frontier manifest creation
- baseline/frontier/challenger challenge runs
- manual frontier promotion from a successful challenge
- markdown reporting

What still remains before a strong registration submission:

- run the benchmark pack with a real agent command
- produce a real baseline-vs-generated result report
- show that PromptForge improves measured task success, not only that the benchmark exists
- add automated challenger submission, queueing, and promotion policy beyond manual CLI use
- add a real prompt search loop instead of only user-supplied challenger prompts
- expand test coverage for the evaluator and reporting logic

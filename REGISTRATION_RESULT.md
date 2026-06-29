# PromptForge Registration Result

## Repo Goal

PromptForge is an objective prompt optimization repo for SN74/Gittensor.

It does not judge prompts by wording quality. It judges them by verified task success on
repo-specific eval tasks.

## Measurement Method

For each eval task, PromptForge compares:

- baseline prompt
- PromptForge-generated repo-specific prompt

under the same:

- repo snapshot
- task definition
- agent command
- evaluation checks

Task success is measured by the task's `checks.sh`, plus path-scope checks from the eval pack.

## Supported Benchmark

First supported repo:

- `e35ventura/taopedia-articles`

Current contributor eval pack:

- `add-delayed-proxies-article`
- `clarify-subnet-77-identity-mapping`
- `clarify-validator-take-vs-stake-weight`

All tasks are pinned to a fixed repo commit through `repo_ref.txt`.

## Real Eval Evidence

Clean real-agent run:

- run id: `e35ventura__taopedia-articles-20260628T201644Z`
- agent: Codex via `scripts/run_codex_eval.sh`

Report summary:

- tasks: `3`
- PromptForge wins: `1`
- baseline wins: `0`
- ties: `2`
- invalid runs: `0`
- PromptForge win rate: `1/3`

Per-task outcome:

- `add-delayed-proxies-article`: tie
- `clarify-subnet-77-identity-mapping`: tie
- `clarify-validator-take-vs-stake-weight`: PromptForge win

## Interpretation

This run shows that PromptForge is not only generating prompts. It is:

- generating repo-specific prompts
- evaluating them on pinned repo tasks
- comparing them against a baseline
- producing objective result artifacts and a report

Current MVP boundary:

- PromptForge now supports a baseline/frontier/challenger workflow with a frontier manifest and
  primary/holdout task pools.
- It is not yet a full multi-candidate prompt-search system or an automated challenger queue.
- The registration value today is the objective evaluation loop and frontier challenge mechanism,
  not a claim of already-complete prompt optimization.

The current benchmark already shows at least one real task where the generated prompt outperformed
the baseline under the same evaluation setup.

## Important Note

After the clean run above, the `clarify-subnet-77-identity-mapping` check was loosened slightly to
avoid brittle exact-phrase matching around equivalent wording such as `registration flow` versus
`registration step`.

That benchmark improvement does not invalidate the measured PromptForge win on
`clarify-validator-take-vs-stake-weight`. It only makes one task check more reliable for future
runs.

## Registration Claim

PromptForge is an objective optimization repo.

Its current registration claim is:

> PromptForge improves repo-specific agent prompts through measured evals on pinned repo tasks,
> rather than subjective prompt wording.

## Source Artifacts

- report: `runs/e35ventura__taopedia-articles-20260628T201644Z/run_summary.json`
- rendered report: `uv run python -m promptforge report --run e35ventura__taopedia-articles-20260628T201644Z`
- eval pack: `evals/e35ventura__taopedia-articles`

from __future__ import annotations

"""Seeded Kata agent for the contributor lane (frontier)."""

import json
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

SEED_INSTRUCTIONS = "# Kata Contributor Seed Instructions: Taopedia Articles\n\nRepo: `taopedia-articles`\nGitHub: `e35ventura/taopedia-articles`\n\nThis seed instruction set is source-grounded from repo files and the configured SN74 registry.\n\n## Repo Overview\n- This repository contains the public MDX article source for Taopedia, a Bittensor-focused knowledge base. (repo:README.md)\n\n## Contribution Rules\n- Use the required front matter. (repo:CONTRIBUTING.md)\n- category: One primary topic. Do not use Bittensor as a catch-all category. (repo:CONTRIBUTING.md)\n- tags: Zero to three specific topic tags. Do not use Bittensor; every published Taopedia article is already Bittensor-focused. (repo:CONTRIBUTING.md)\n- Keep sentences direct; do not use a long explanation when a short one preserves the meaning. (repo:CONTRIBUTING.md)\n- Sources are required for factual and technical claims. AI-assisted writing is allowed, but unsourced writing is not. (repo:CONTRIBUTING.md)\n- Do not use generic homepages, SEO pages, social posts, or screenshots as support for technical claims unless they are clearly marked as context and no stronger source exists. (repo:CONTRIBUTING.md)\n- Every section should add a new fact, distinction, caveat, source, or operational detail. (repo:CONTRIBUTING.md)\n- When docs and code disagree, code is the source of truth for implementation behavior. Docs can support conceptual explanations, but exact mechanics should be backed by code, release notes, or official specs. (repo:CONTRIBUTING.md)\n\n## Validation Commands\n- `npm run format:check` (repo:CONTRIBUTING.md)\n- `npm run validate` (repo:CONTRIBUTING.md)\n\n## Protected Paths\n- Repository-wide ownership rules exist (`*`). (repo:.github/CODEOWNERS)\n\n## Kata PR Checklist\n- Run the most relevant validation commands above before opening the PR. (repo:CONTRIBUTING.md)\n- Avoid changing protected or maintainer-owned paths unless explicitly intended. (repo:.github/CODEOWNERS)\n- Include the required visual evidence for visible UI changes. (repo:CONTRIBUTING.md)\n\n## Scoring / Registry Notes\n- Registry entry found for `e35ventura/taopedia-articles`. (https://raw.githubusercontent.com/entrius/gittensor/test/gittensor/validator/weights/master_repositories.json)\n- `emission_share`: `0.025` (https://raw.githubusercontent.com/entrius/gittensor/test/gittensor/validator/weights/master_repositories.json)\n- `trusted_label_pipeline`: `True` (https://raw.githubusercontent.com/entrius/gittensor/test/gittensor/validator/weights/master_repositories.json)\n- `label_multipliers`: article=1.0, correction=1.25, image=0.75, category=0.5, other=0.1 (https://raw.githubusercontent.com/entrius/gittensor/test/gittensor/validator/weights/master_repositories.json)\n- `eligibility`: min_credibility=0.7, min_token_score_for_valid_issue=0.0 (https://raw.githubusercontent.com/entrius/gittensor/test/gittensor/validator/weights/master_repositories.json)\n\n## Unknowns / Caveats\n- No major source gaps were detected in the current scan.\n\n## Sources\n- https://github.com/e35ventura/taopedia-articles.git@baa3ebab1a533cfdf4b114bc180b69df3c365051\n- repo:README.md\n- repo:CONTRIBUTING.md\n- repo:.github/CODEOWNERS\n- repo:.github/workflows/build-index.yml\n- repo:.github/workflows/pr-source-check.yml\n- repo:.github/workflows/release.yml\n- repo:.github/workflows/trigger-taopedia-deploy.yml\n- repo:.github/workflows/validate-content.yml\n- https://raw.githubusercontent.com/entrius/gittensor/test/gittensor/validator/weights/master_repositories.json\n"
LANE_MODE = "contributor"
AGENT_LABEL = "frontier"
MAX_CONTEXT_CHARS = 52000
MAX_FILE_CHARS = 14000
MAX_REFERENCE_FILE_CHARS = 6000
MAX_REFERENCE_FILES = 2
ARTICLE_PATH_PATTERN = re.compile(r"content/pages/[A-Za-z0-9_./-]+")
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")
STOP_WORDS = {
    "a",
    "add",
    "an",
    "and",
    "article",
    "be",
    "content",
    "correct",
    "edit",
    "expected",
    "file",
    "for",
    "goal",
    "green",
    "in",
    "index",
    "mdx",
    "must",
    "of",
    "or",
    "outcome",
    "page",
    "pages",
    "path",
    "pinned",
    "repo",
    "repository",
    "scoped",
    "snapshot",
    "so",
    "stay",
    "task",
    "the",
    "to",
    "update",
    "validation",
}
STATIC_CONTEXT_PATHS = (
    "CONTRIBUTING.md",
    "package.json",
    ".github/CODEOWNERS",
)
TASK_EXECUTION_RULES = """\
Execution rules for this repo:
- Prefer the exact article path named in the task when one is provided.
- Keep edits tightly scoped; avoid broad rewrites or unrelated file changes.
- Preserve valid front matter and fix it if it is incomplete or malformed.
- Keep prose factual, concise, and Bittensor-focused.
- Prefer official docs, code, release notes, and primary sources for claims.
- Use wiki-style internal links like [[Article Title]] instead of normal relative article links.
- Return only a unified diff.
"""


def solve(repo_path: str, issue: str, model: str, api_base: str, api_key: str) -> dict:
    if not model:
        return {
            "success": False,
            "message": "validator did not provide a model",
            "diff": "",
        }
    if not api_base:
        return {
            "success": False,
            "message": "validator did not provide an api_base",
            "diff": "",
        }

    repo_root = Path(repo_path).resolve()
    tracked_files = list_tracked_files(repo_root)
    target_paths = extract_target_paths(issue, tracked_files)
    repo_context = build_repo_context(
        repo_root=repo_root,
        issue=issue,
        tracked_files=tracked_files,
        target_paths=target_paths,
    )
    response_text = request_diff(
        model=model,
        api_base=api_base,
        api_key=api_key,
        issue=issue,
        repo_context=repo_context,
        target_paths=target_paths,
    )
    diff_text = normalize_diff(response_text)
    if not diff_text:
        return {
            "success": False,
            "message": "model did not return an applicable unified diff",
            "diff": "",
        }
    scope_errors = validate_diff_scope(diff_text, target_paths)
    if scope_errors:
        return {
            "success": False,
            "message": "; ".join(scope_errors),
            "diff": "",
        }
    return {
        "success": True,
        "message": f"{AGENT_LABEL} seed agent produced a diff",
        "diff": diff_text,
    }


def list_tracked_files(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def extract_target_paths(issue: str, tracked_files: list[str]) -> list[str]:
    tracked = set(tracked_files)
    targets: list[str] = []
    seen: set[str] = set()
    for match in ARTICLE_PATH_PATTERN.findall(issue):
        candidate = normalize_candidate_path(match)
        if candidate in tracked and candidate not in seen:
            seen.add(candidate)
            targets.append(candidate)
            continue
        article_candidate = candidate.rstrip("/") + "/index.mdx"
        if article_candidate in tracked and article_candidate not in seen:
            seen.add(article_candidate)
            targets.append(article_candidate)
    if targets:
        return targets

    issue_tokens = extract_issue_tokens(issue)
    ranked_articles = rank_article_paths(issue_tokens, tracked_files)
    return ranked_articles[:1]


def normalize_candidate_path(value: str) -> str:
    return value.strip().strip("`'\"()[]{}<>.,:;")


def extract_issue_tokens(issue: str) -> set[str]:
    tokens: set[str] = set()
    for raw in TOKEN_PATTERN.findall(issue.lower().replace("-", "_")):
        parts = [part for part in raw.split("_") if part]
        for part in parts:
            if len(part) < 3 or part in STOP_WORDS:
                continue
            tokens.add(part)
    return tokens


def rank_article_paths(issue_tokens: set[str], tracked_files: list[str]) -> list[str]:
    article_paths = [
        path
        for path in tracked_files
        if path.startswith("content/pages/") and path.endswith("/index.mdx")
    ]
    ranked = sorted(
        article_paths,
        key=lambda path: (
            article_match_score(path, issue_tokens),
            path,
        ),
        reverse=True,
    )
    return [path for path in ranked if article_match_score(path, issue_tokens) > 0]


def article_match_score(path: str, issue_tokens: set[str]) -> int:
    if not issue_tokens:
        return 0
    path_tokens = extract_issue_tokens(path)
    overlap = len(path_tokens & issue_tokens)
    slug = path.split("/")[2] if path.count("/") >= 2 else path
    title_bonus = 2 if slug.lower() in issue_tokens else 0
    return overlap * 10 + title_bonus


def build_repo_context(
    *,
    repo_root: Path,
    issue: str,
    tracked_files: list[str],
    target_paths: list[str],
) -> str:
    focus_files = select_focus_files(issue, tracked_files, target_paths)
    sections: list[str] = []
    if target_paths:
        sections.append("## Target Paths")
        sections.extend(f"- {path}" for path in target_paths)
        sections.append("")
    sections.append("## Focus Files")
    sections.extend(f"- {path}" for path in focus_files)
    sections.append("")
    sections.append("## Available Article Slugs")
    sections.append(render_article_slug_list(tracked_files))
    sections.append("")
    sections.append("## File Contents")
    file_sections = render_file_sections(repo_root, focus_files, target_paths)
    sections.append(file_sections or "(no file contents captured)")
    return "\n".join(sections).strip()


def select_focus_files(issue: str, tracked_files: list[str], target_paths: list[str]) -> list[str]:
    tracked = set(tracked_files)
    focus: list[str] = []
    seen: set[str] = set()

    def add(path: str) -> None:
        if path in tracked and path not in seen:
            seen.add(path)
            focus.append(path)

    for path in STATIC_CONTEXT_PATHS:
        add(path)
    for path in target_paths:
        add(path)

    issue_tokens = extract_issue_tokens(issue)
    for path in rank_article_paths(issue_tokens, tracked_files):
        if path in target_paths:
            continue
        add(path)
        if len([item for item in focus if item.startswith("content/pages/")]) >= (
            len(target_paths) + MAX_REFERENCE_FILES
        ):
            break
    return focus


def render_article_slug_list(tracked_files: list[str]) -> str:
    slugs = sorted(
        {
            path.split("/")[2]
            for path in tracked_files
            if path.startswith("content/pages/") and path.endswith("/index.mdx")
        }
    )
    if not slugs:
        return "(no article slugs found)"
    if len(slugs) > 80:
        slugs = slugs[:80]
    return ", ".join(slugs)


def render_file_sections(repo_root: Path, focus_files: list[str], target_paths: list[str]) -> str:
    sections: list[str] = []
    total_chars = 0
    target_set = set(target_paths)
    for relative_path in focus_files:
        absolute_path = repo_root / relative_path
        if not absolute_path.is_file():
            continue
        max_chars = MAX_FILE_CHARS if relative_path in target_set else MAX_REFERENCE_FILE_CHARS
        content = read_text_excerpt(absolute_path, max_chars=max_chars)
        if not content:
            continue
        section = f"### FILE: {relative_path}\n```\n{content}\n```"
        if total_chars + len(section) > MAX_CONTEXT_CHARS:
            break
        sections.append(section)
        total_chars += len(section)
    return "\n\n".join(sections)


def read_text_excerpt(path: Path, *, max_chars: int) -> str:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""
    content = content.strip()
    if len(content) <= max_chars:
        return content
    return content[:max_chars].rstrip() + "\n...[truncated]"


def request_diff(
    *,
    model: str,
    api_base: str,
    api_key: str,
    issue: str,
    repo_context: str,
    target_paths: list[str],
) -> str:
    system_prompt = (
        "You are a repo-specific coding agent for Kata. "
        "Return only a unified diff that can be applied with git apply. "
        "Do not return prose, markdown fences, or explanations.\n\n"
        f"{TASK_EXECUTION_RULES}\n"
        "Repo-specific instructions:\n"
        f"{SEED_INSTRUCTIONS}"
    )
    target_text = "\n".join(f"- {path}" for path in target_paths) if target_paths else "- none detected"
    user_prompt = (
        f"Lane mode: {LANE_MODE}\n\n"
        "Explicit target paths:\n"
        f"{target_text}\n\n"
        "Task:\n"
        f"{issue.strip()}\n\n"
        f"{repo_context}\n\n"
        "Output requirement: return only the final unified diff."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 2000,
    }
    request = urllib.request.Request(
        build_chat_completions_url(api_base),
        data=json.dumps(payload).encode("utf-8"),
        headers=build_headers(api_key),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"chat completion request failed: {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"chat completion request failed: {exc.reason}") from exc
    return extract_message_content(response_payload)


def build_chat_completions_url(api_base: str) -> str:
    base = api_base.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return base + "/chat/completions"


def build_headers(api_key: str) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def extract_message_content(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return str(content)


def normalize_diff(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    diff_index = text.find("diff --git")
    if diff_index == -1:
        diff_index = text.find("--- ")
    if diff_index != -1:
        return text[diff_index:].rstrip() + "\n"
    return ""


def validate_diff_scope(diff_text: str, target_paths: list[str]) -> list[str]:
    if not target_paths:
        return []
    changed_paths = parse_changed_paths(diff_text)
    if not changed_paths:
        return ["model returned a diff without parseable changed file paths"]
    disallowed = sorted(path for path in changed_paths if path not in target_paths)
    if not disallowed:
        return []
    return [
        "model proposed edits outside the named task path: " + ", ".join(disallowed)
    ]


def parse_changed_paths(diff_text: str) -> list[str]:
    changed: list[str] = []
    seen: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                candidate = normalize_diff_path(parts[3])
                if candidate and candidate not in seen:
                    seen.add(candidate)
                    changed.append(candidate)
        elif line.startswith("+++ "):
            candidate = normalize_diff_path(line[4:].strip())
            if candidate and candidate not in seen:
                seen.add(candidate)
                changed.append(candidate)
    return changed


def normalize_diff_path(value: str) -> str | None:
    if value == "/dev/null":
        return None
    path = value
    if path.startswith("a/") or path.startswith("b/"):
        path = path[2:]
    return path.strip()

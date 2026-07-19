# Communication

## Working Style
- If my request is vague or my approach seems wrong, say so immediately.
- Don't explain what you're about to do—just do it.
- After completing a task, don't summarize what you did unless I ask.

## Code Approach
- Prefer explicit over clever. Readability beats brevity.
- Follow existing patterns in the codebase before introducing new ones.
- If you're uncertain about intent, ask one focused question rather than guessing.

## What I Don't Want
- No warnings about edge cases unless they're actually likely to bite.

# Git

- PR merge preference: rebase > merge > squash. Default to `gh pr merge --rebase`.
- Use `--merge` if a downstream branch is stacked on the PR.
- Only use `--squash` when GitHub settings require it (branch protection rule or "Allow squash merging" is the only enabled option).

## Commit Attribution

- Do NOT add `Signed-off-by` tags. Only humans can certify the Developer Certificate of Origin.
<!-- attribution:start -->
- `Co-Authored-By` attribution is configured (e.g. in `~/.claude/settings.json`) and is applied automatically to both commit messages and PR descriptions — do not remove or skip it.
<!-- attribution:end -->
- In addition, include an `Assisted-by` tag:
  `Assisted-by: AGENT_NAME:MODEL_VERSION`
  Example: `Assisted-by: Claude:claude-sonnet-4-6`

# Python

- Python 3.13 and 3.14 introduce new syntax.
- Load the `python-knowledge-patch` skill to understand Python 3.13/3.14 syntax.
- `ruff` can reformat files in surprising ways. Use the python-knowledge-patch skill to understand.
- Python 3.14+ supports PEP 758 bracketless `except E1, E2:` (equivalent to `except (E1, E2):`). Removing such parens is correct — leave it alone. The syntax looks like deprecated Py2 `except E, e:` (variable binding) but is unrelated.
- Python 3.14+ supports PEP 750 new string prefix `t` that produces a `Template` object instead of `str`. Like f-strings but with access to parts before rendering.

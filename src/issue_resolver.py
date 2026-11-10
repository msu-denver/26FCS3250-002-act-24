#!/usr/bin/env python3
"""
Agent that resolves the oldest open GitHub issue of a project repository.

Workflow:
  1. Look up the oldest open issue via the GitHub REST API.
  2. Create a branch for it from dev and ask the local GitHub Copilot CLI to make the
     minimal code change(s) needed to fix it, following the
     .github/copilot-instructions.json file in the current folder.
  3. Commit, push, and open a pull request ("Closes #<n>") targeting the
     repo's dev branch.
  4. Comment on the issue with a link to the pull request.

The agent lives outside the project repository it works on. Run it from a
folder outside the project (e.g., the agent folder) and point it at the
project with --repo.

Authentication:
  Reads GITHUB_TOKEN from a `.secrets` file (KEY=VALUE per line) in the
  current folder (the folder the agent is run from). The agent refuses to run
  if that file is inside the project repository, so the token can neither be
  committed nor read by Copilot, which works inside the project.

Usage:
  python3 issue_resolver.py --repo PATH [--verbose]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
SECRETS_FILE = Path.cwd() / ".secrets"  # read from the folder the agent is run from
INSTRUCTIONS_FILE = Path.cwd() / ".github" / "copilot-instructions.json"  # read from the folder the agent is run from
GITHUB_API = "https://api.github.com"
BASE_BRANCH = "dev"  # fix branches are created from, and PRs target, this branch
TOTAL_STEPS = 8

# Copilot runs non-interactively (-p), so any tool request not allowed below is
# denied automatically. Commands Copilot recognizes as read-only (ls, cat, grep,
# ...) run without a rule. Deny rules always win over allow rules.
COPILOT_PERMISSIONS = [
    "--allow-tool", "write",               # create and edit files
    "--allow-tool", "shell(pytest:*)",     # run the test suite
    "--deny-tool", "shell(git:*)",         # the resolver handles git
    "--deny-tool", "shell(gh:*)",          # the resolver handles GitHub
    "--deny-tool", "shell(pip:*)",         # no package installs
    "--deny-tool", "shell(pip3:*)",
    "--deny-tool", "shell(curl:*)",        # no network access
    "--deny-tool", "shell(wget:*)",
    "--deny-tool", "read(.secrets)",       # never expose the GitHub token
    "--deny-tool", "write(.secrets)",
    "--deny-tool", "write(.github/copilot-instructions.json)",
    "--deny-tool", "write(app/static/style.css)",  # the provided stylesheet is read-only
]
VERBOSE = False  # set by --verbose
START_TIME = time.monotonic()


def elapsed() -> str:
    seconds = int(time.monotonic() - START_TIME)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def step(number: int, message: str) -> None:
    # Announces the start of one of the agent's main steps.
    print(f"\n[{elapsed()}] Step {number}/{TOTAL_STEPS}: {message}", flush=True)


def info(message: str) -> None:
    print(f"           {message}", flush=True)


def debug(message: str) -> None:
    # Only shown with --verbose.
    if VERBOSE:
        print(f"           [debug] {message}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve the oldest open GitHub issue of a project using GitHub Copilot."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        required=True,
        help="path to the project's cloned repository (must not contain the current folder)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="also show every git command, GitHub API call, and the full prompt sent to Copilot",
    )
    return parser.parse_args()


def load_secrets(path: Path) -> dict:
    secrets = {}
    if not path.exists():
        return secrets
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        secrets[key.strip()] = value.strip()
    return secrets


def ensure_secrets_outside_repo(repo: Path) -> None:
    # A .secrets file inside the project could be committed by `git add -A`,
    # and Copilot, which works inside the project, could read it with a shell
    # command such as `cat` (Copilot's read(...) rules only cover its file
    # tools). So the agent must be run from a folder outside the project.
    if Path.cwd().resolve().is_relative_to(repo.resolve()):
        sys.exit(
            f"The current folder ({Path.cwd()}) is inside the project repository ({repo}), "
            "so its .secrets file would be exposed to Copilot and could be committed.\n"
            "Run the agent from a folder outside the project (e.g., the agent folder) "
            "and point it at the project with --repo."
        )


def get_github_token() -> str:
    token = load_secrets(SECRETS_FILE).get("GITHUB_TOKEN")
    if not token:
        sys.exit(f"GITHUB_TOKEN not found in {SECRETS_FILE}")
    return token


def run_git(repo: Path, *args, check=True):
    debug(f"$ git {' '.join(args)}")
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
    )
    output = (result.stdout + result.stderr).strip()
    if output:
        debug(output)
    if check and result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed (exit code {result.returncode}):\n{output}")
    return result


def find_repo_root(path: Path) -> Path:
    # Accepts the repository's main folder or any folder inside it.
    if not path.is_dir():
        sys.exit(f"Folder not found: {path}")
    result = run_git(path, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        sys.exit(f"Not a git repository: {path.resolve()}")
    repo = Path(result.stdout.strip())
    if repo == AGENT_DIR or AGENT_DIR.is_relative_to(repo):
        sys.exit(
            f"{repo} contains the agent itself. Point --repo at your project's "
            "repository, not at the agent's."
        )
    return repo


def get_repo_slug(repo: Path) -> str:
    result = run_git(repo, "remote", "get-url", "origin", check=False)
    if result.returncode != 0:
        sys.exit(f"The repository at {repo} has no 'origin' remote.")
    url = result.stdout.strip()
    match = re.search(r"github\.com[:/]([^/]+)/([^/.]+?)(\.git)?$", url)
    if not match:
        sys.exit(f"Could not parse a GitHub owner/repo from remote URL: {url}")
    return f"{match.group(1)}/{match.group(2)}"


def github_request(method: str, path: str, token: str, data: dict = None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(f"{GITHUB_API}{path}", data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    debug(f"GitHub API {method} {path}")
    try:
        with urllib.request.urlopen(req) as resp:
            debug(f"GitHub API responded {resp.status}")
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        message = f"GitHub API error {e.code} for {method} {path}: {e.read().decode()}"
        if e.code in (401, 403):
            message += (
                "\n\nThe GitHub token in .secrets is missing a permission. Check that it:\n"
                "  - has the repository's owner (your account, or the organization if the\n"
                "    repository belongs to one) as its Resource owner;\n"
                "  - has been approved by the organization, if the organization requires it;\n"
                "  - includes this repository under Repository access;\n"
                "  - has Issues and Pull requests set to Read and write, and Contents set\n"
                "    to at least Read-only;\n"
                "  - has not expired.\n"
                "See the README's GitHub Token section."
            )
        sys.exit(message)
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach the GitHub API for {method} {path}: {e.reason}")


def get_oldest_open_issue(repo_slug: str, token: str) -> dict | None:
    issues = github_request(
        "GET",
        f"/repos/{repo_slug}/issues?state=open&sort=created&direction=asc&per_page=30",
        token,
    )
    open_issues = [i for i in issues if "pull_request" not in i]  # the endpoint also returns PRs
    info(f"Found {len(open_issues)} open issue(s) (skipped {len(issues) - len(open_issues)} pull request(s)).")
    for issue in open_issues:
        debug(f"#{issue['number']} (created {issue['created_at']}): {issue['title']}")
    return open_issues[0] if open_issues else None


def create_fix_branch(repo: Path, issue_number: int, base_branch: str) -> str:
    branch = f"issue-{issue_number}-fix"
    info(f"Fetching origin/{base_branch}...")
    run_git(repo, "fetch", "origin", base_branch)
    base_commit = run_git(repo, "log", "-1", "--format=%h %s", f"origin/{base_branch}").stdout.strip()
    info(f"Creating branch {branch} from origin/{base_branch} ({base_commit}).")
    run_git(repo, "checkout", "-B", branch, f"origin/{base_branch}")
    return branch


def load_agent_instructions() -> str:
    # Read before switching to the fix branch: if the agent is run from inside
    # the project, switching branches could change or remove the file.
    instructions_file = INSTRUCTIONS_FILE
    if not instructions_file.exists():
        sys.exit(f"Agent instructions not found: {instructions_file}")
    text = instructions_file.read_text().strip()
    try:
        json.loads(text)
    except json.JSONDecodeError as e:
        sys.exit(f"Agent instructions are not valid JSON ({instructions_file}): {e}")
    info(f"Loaded {instructions_file} ({len(text)} characters).")
    return text


def resolve_with_copilot(repo: Path, issue: dict, instructions: str) -> None:
    prompt = (
        "Follow these project instructions (JSON) for every change you make:\n\n"
        "<instructions>\n"
        f"{instructions}\n"
        "</instructions>\n\n"
        f"Resolve GitHub issue #{issue['number']} in this repository.\n\n"
        f"Title: {issue['title']}\n\n"
        f"Description:\n{issue.get('body') or '(no description provided)'}\n\n"
        "Make the minimal code change(s) needed to satisfy every acceptance "
        "criterion of this issue, as described in the instructions' task section. "
        "Do not commit, push, or open a pull request yourself -- only edit files."
    )
    info(f"Prompt: {len(prompt)} characters (instructions + issue #{issue['number']}).")
    if VERBOSE:
        debug("Full prompt:\n" + prompt)
    # Run the GitHub Copilot CLI non-interactively (-p) inside the project
    # repository, with the tool permissions in COPILOT_PERMISSIONS. Its output
    # is streamed to the console as it is produced, so you can follow it.
    if shutil.which("pytest") is None:
        info("Warning: pytest was not found on PATH, so Copilot will not be able to run the "
             "tests. Activate the project's virtual environment before running the agent.")
    # Keep test runs from leaving files behind (.pytest_cache, __pycache__),
    # since every change in the working tree is committed.
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_ADDOPTS="-p no:cacheprovider")
    debug("Copilot permissions: " + " ".join(COPILOT_PERMISSIONS))
    info("Running GitHub Copilot CLI; this can take several minutes. Copilot's output follows.")
    print("-" * 30 + " copilot " + "-" * 30, flush=True)
    copilot_start = time.monotonic()
    try:
        result = subprocess.run(
            ["copilot", "-p", prompt, *COPILOT_PERMISSIONS],
            cwd=str(repo),
            env=env,
            text=True,
        )
    except FileNotFoundError:
        sys.exit(
            "GitHub Copilot CLI not found. Install it as described in the "
            "README's GitHub Copilot CLI section, then run `copilot` once to log in."
        )
    print("-" * 69, flush=True)
    info(f"Copilot finished in {int(time.monotonic() - copilot_start)}s (exit code {result.returncode}).")
    if result.returncode != 0:
        sys.exit("GitHub Copilot CLI failed to run; see its output above.")


def changed_files(repo: Path) -> list[str]:
    # Untracked folders are listed file by file (-uall) so every new file shows up.
    return run_git(repo, "status", "--porcelain", "-uall").stdout.splitlines()


def commit_and_push(repo: Path, branch: str, issue: dict) -> None:
    message = f"Fix #{issue['number']}: {issue['title']}"
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-m", message)
    commit = run_git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    info(f"Committed {commit}: {message}")
    info(f"Pushing {branch} to origin...")
    run_git(repo, "push", "-u", "origin", branch)
    info("Pushed.")


def open_pull_request(repo_slug: str, token: str, branch: str, base_branch: str, issue: dict) -> dict:
    data = {
        "title": f"Fix #{issue['number']}: {issue['title']}",
        "head": branch,
        "base": base_branch,
        "body": f"Closes #{issue['number']}\n\nAutomated fix generated by issue_resolver.py.",
    }
    return github_request("POST", f"/repos/{repo_slug}/pulls", token, data)


def comment_on_issue(repo_slug: str, token: str, issue: dict, pr: dict) -> None:
    github_request(
        "POST",
        f"/repos/{repo_slug}/issues/{issue['number']}/comments",
        token,
        {"body": f"Opened pull request {pr['html_url']} to resolve this issue."},
    )


def main() -> None:
    global VERBOSE
    args = parse_args()
    VERBOSE = args.verbose

    step(1, "Working out which repository to use")
    repo = find_repo_root(args.repo)
    repo_slug = get_repo_slug(repo)
    info(f"Project folder: {repo}")
    info(f"GitHub repository: {repo_slug}")

    step(2, "Loading the GitHub token")
    ensure_secrets_outside_repo(repo)
    token = get_github_token()
    info(f"Read GITHUB_TOKEN from {SECRETS_FILE}.")

    step(3, "Picking the oldest open issue")
    issue = get_oldest_open_issue(repo_slug, token)
    if issue is None:
        info("No open issues found. Nothing to do.")
        return
    info(f"Selected issue #{issue['number']}: {issue['title']}")
    info(f"URL: {issue['html_url']}")

    step(4, "Loading the agent instructions")
    instructions = load_agent_instructions()

    step(5, f"Creating a fix branch from {BASE_BRANCH}")
    original_branch = run_git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    info(f"Current branch: {original_branch}")
    branch = create_fix_branch(repo, issue["number"], BASE_BRANCH)

    step(6, f"Asking GitHub Copilot to resolve issue #{issue['number']}")
    resolve_with_copilot(repo, issue, instructions)

    step(7, "Checking for changes")
    changes = changed_files(repo)
    if not changes:
        info("GitHub Copilot made no changes; nothing to commit.")
        info(f"Switching back to {original_branch} and deleting {branch}.")
        run_git(repo, "checkout", original_branch)
        run_git(repo, "branch", "-D", branch)
        return
    info(f"{len(changes)} file(s) changed:")
    for line in changes:
        info(f"  {line}")

    step(8, "Committing, pushing, and opening a pull request")
    commit_and_push(repo, branch, issue)
    pr = open_pull_request(repo_slug, token, branch, BASE_BRANCH, issue)
    info(f"Opened pull request #{pr['number']}: {pr['html_url']}")
    comment_on_issue(repo_slug, token, issue, pr)
    info(f"Commented on issue #{issue['number']} with a link to the pull request.")

    print(f"\n[{elapsed()}] Done. Review and merge the pull request: {pr['html_url']}", flush=True)


if __name__ == "__main__":
    main()

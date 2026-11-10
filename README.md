# Overview

In this activity you will follow an agentic development lifecycle: you will use an AI software development agent to implement the code and the tests for a web application.

# Requirements

This section describes user stories for the web application that you will develop with the help of an AI agent. These are the same user stories you worked with in your first project this semester, plus two new ones: user registration (User Story 1) and adding a completed course (User Story 3).

## User Story 1: User Registration

As a student,\
I want to register for an account,\
so that I can access the system.

**Acceptance Criteria**

- [ ] Given an unregistered student, when the student submits a student ID, full name, email address, and password, then a new student account is created and the student can log in with those credentials.
- [ ] Given a registration request, when any required field is missing or invalid (e.g., a malformed email address or a password shorter than 8 characters), then the account is not created and an appropriate error message is displayed.
- [ ] Given an existing account, when a student attempts to register with the same student ID or email address, then the account is not created and an appropriate error message is displayed.
- [ ] Given a successful registration, when the account is stored, then the password is not stored in plain text.

## User Story 2: User Authentication

As a student,\
I want to authenticate myself,\
so that I can securely access my academic information.

**Acceptance Criteria**

- [ ] Given a registered student account, when valid credentials are entered, then the student is granted access to the system.
- [ ] Given invalid credentials, when a login attempt is made, then an appropriate error message is displayed.
- [ ] Given an authenticated student, when the student logs out, then access to protected features is terminated.

## User Story 3: Add a Completed Course

As a student,\
I want to add a completed course and the letter grade I earned,\
so that my academic history and GPA are complete.

**Acceptance Criteria**

- [ ] Given an authenticated student, when the student submits a course identifier, course name, credit hours, and letter grade, then the course is added to the student's completed courses and displayed in the list.
- [ ] Given a new course, when any required field is missing, the credit hours are not a positive whole number, or the letter grade is not one of A, B, C, D, or F, then the course is not added and an appropriate error message is displayed.
- [ ] Given a student who has already recorded a course with the same course identifier, when the student attempts to add it again, then the course is not added and an appropriate error message is displayed.
- [ ] Given a successfully added course, when it is saved, then the GPA is recalculated and updated accordingly.

## User Story 4: View Previously Completed Courses

As a student,\
I want to view all previously completed courses,\
so that I can review my academic history.

**Acceptance Criteria**

- [ ] Given an authenticated student, when the student requests completed courses, then all previously completed courses are displayed.
- [ ] Given a list of completed courses, when it is displayed, then each course listing includes the course identifier, course name, credit hours, and earned letter grade.
- [ ] Given an authenticated student with no completed courses, when the student requests completed courses, then an appropriate message is displayed.

## User Story 5: View Current GPA

As a student,\
I want to view my current GPA,\
so that I can monitor my academic performance.

**Acceptance Criteria**

- [ ] Given an authenticated student, when the student views their completed courses, then the current GPA is displayed.
- [ ] Given the completed courses currently stored in the system, when the GPA is calculated, then it is the credit-hour-weighted average of the grade points of all completed courses, using the scale A = 4, B = 3, C = 2, D = 1, F = 0.
- [ ] Given a calculated GPA, when it is displayed, then it is shown with two decimal places.
- [ ] Given an authenticated student with no completed courses, when the student views their completed courses, then a message indicating that no GPA is available is displayed.

## User Story 6: Update a Course Grade

As a student,\
I want to update the letter grade for a completed course,\
so that I can correct my academic records.

**Acceptance Criteria**

- [ ] Given an authenticated student, when the student selects a completed course, then the student can edit the letter grade.
- [ ] Given a grade update, when the new letter grade is one of A, B, C, D, or F, then the update is accepted and the modified grade is displayed.
- [ ] Given a grade update, when the new letter grade is not one of A, B, C, D, or F, then the update is rejected and an appropriate error message is displayed.
- [ ] Given a successful grade update, when the update is saved, then the GPA is recalculated and updated accordingly.

## User Story 7: Delete a Completed Course

As a student,\
I want to delete a previously completed course,\
so that I can remove courses that should no longer be included in my records.

**Acceptance Criteria**

- [ ] Given an authenticated student, when the student selects a completed course, then the student can request its deletion.
- [ ] Given a deletion request, when the request is made, then the system asks for confirmation before permanently deleting the course.
- [ ] Given a deletion request, when the student confirms, then the selected course is removed from the list of completed courses and the GPA is recalculated and updated accordingly.
- [ ] Given a deletion request, when the student cancels, then the course is not deleted.

# GitHub Repository

Create a **new** GitHub repository for this project under your **personal** GitHub account, not under an organization (e.g., `msu-denver`). Do not reuse the repository of your first project, even though the user stories are similar: this project's code will be written by an AI agent, or by you with AI assistance, so it must start from an empty repository and be kept separate from the code you wrote earlier. It must also be separate from this activity's repository, which contains the agent itself.

Then, create an **issue** for each of the user stories above, using the user story title as the issue title and its acceptance criteria as a checklist in the issue body.

Once you are done, sort the issue list in chronological order (oldest first).

Do all of these steps using GitHub's web interface.

# Development Environment Setup

Next, set up the development environment in which the AI agent will work.

## Project Repository

Begin by cloning the project's repository and creating the `main` branch:

```bash
git clone https://github.com/<your-username>/<your-repository>.git
cd <your-repository>
git switch -c main
git commit --allow-empty -m "Initial commit"
git push -u origin main
```

If you created the repository with a README, the `main` branch already exists, so you can skip the last three commands.

Next, add the application's stylesheet. The file `static/style.css` in your assignment repository gives every page a consistent, modern look (with light and dark themes), and the agent instructions tell Copilot to use it without changing it. Copy it into your project's repository and commit it to `main` (if you have not cloned your assignment repository yet, see [Assignment Repository](#assignment-repository)):

```bash
mkdir -p app/static
cp <path-to-assignment-repository>/static/style.css app/static/style.css
git add app/static/style.css
git commit -m "Add stylesheet"
git push
```

On Windows (PowerShell), replace the first two commands with:

```powershell
New-Item -ItemType Directory -Force app\static
Copy-Item <path-to-assignment-repository>\static\style.css app\static\style.css
```

Then, create the `dev` branch:

```bash
git switch -c dev
git push -u origin dev
```

## GitHub CLI

GitHub CLI (`gh`) provides programmatic access to GitHub from the command line. Follow the [GitHub CLI installation instructions](https://cli.github.com/) to download and install it in your environment. Verify the installation by running:

```bash
gh --version
```

Complete your setup by authenticating with GitHub:

```bash
gh auth login
```

## Assignment Repository

The issue resolver agent (`src/issue_resolver.py`) is already in your assignment repository (this activity's repository), which is separate from your project's repository, so the agent never becomes part of the code it works on. You will run the agent from the root folder of your assignment repository (see [Issue Resolver Agent](#issue-resolver-agent)). If you have not cloned it yet, do so now, **outside** your project's repository.

## Agent Instructions

The file `.github/copilot-instructions.json` tells the AI agent which technology stack, project structure, and conventions to use (Python, Flask, SQLAlchemy, and SQLite), including that every page must be styled with `app/static/style.css`. The agent reads it from the `.github` folder of the folder you run the agent from (the root of your assignment repository; see [Issue Resolver Agent](#issue-resolver-agent)), not from your project's repository. It is already in your assignment repository, so there is nothing to copy.

## GitHub Token

The AI agent needs an access token to call the GitHub API. To create one on GitHub's web interface:

1. Click your profile icon, then go to **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. Name the token **act-24**.
3. Under **Resource owner**, select your personal account (the owner of your project's repository).
4. Under **Repository access**, select **Only select repositories** and choose your project's repository.
5. Under **Permissions**, set **Issues** and **Pull requests** to **Read and write**, and **Contents** to **Read-only**.
6. Click **Generate token** and copy it.

Then, create a `.secrets` file in the folder you will run the agent from (the root of your assignment repository, `<path-to-assignment-repository>/.secrets`; see [Issue Resolver Agent](#issue-resolver-agent)) with the following entry:

```
GITHUB_TOKEN=<paste your token here>
```

The assignment repository's `.gitignore` already excludes `.secrets`, so it will not be committed there. Never put the `.secrets` file in your project's repository: it could be committed, and anyone who can see the repository would be able to use your token. Copilot, which works inside the project, could also read it. The agent refuses to run from a folder inside your project's repository for this reason.

## GitHub Copilot CLI

The agent uses the GitHub Copilot CLI (`copilot`) to make code changes, so you need an active GitHub Copilot subscription. Note that the Copilot extension for VS Code does not install the CLI; it must be installed separately.

On **macOS**, install it with [Homebrew](https://brew.sh/):

```bash
brew install copilot-cli
```

On **Windows**, install it from PowerShell or Command Prompt with WinGet:

```powershell
winget install GitHub.Copilot
```

Verify the installation by running:

```bash
copilot --version
```

Finally, run `copilot` once and follow the instructions to log in with your GitHub account. If you run into problems, see GitHub's [Copilot CLI installation instructions](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli).

You may use another AI agent tool of your preference, but you will then need to change how the agent calls it (see the `resolve_with_copilot()` function).

## Python Virtual Environment

Copilot runs the project's tests with `pytest` while it works, but it is not allowed to install packages. Create a virtual environment with the project's dependencies, and activate it before running the agent. Create it in your assignment repository, **not** in your project's repository: the agent commits every file in the project's folder, so a virtual environment there would be committed.

On **macOS**:

```bash
cd <path-to-assignment-repository>
python3 -m venv .venv
source .venv/bin/activate
pip install flask flask-sqlalchemy pytest
```

On **Windows** (PowerShell):

```powershell
cd <path-to-assignment-repository>
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install flask flask-sqlalchemy pytest
```

If a later issue adds a dependency to the project's `requirements.txt`, install it with `pip install -r <path-to-your-repository>/requirements.txt` before running the agent again. If `pytest` is not found when the agent runs, it prints a warning and Copilot can only check the tests by reading them.

# Issue Resolver Agent

This section explains, step by step, how the issue resolver agent (`issue_resolver.py`) works. Each run resolves one issue. To run it, activate the virtual environment, go to the root of your assignment repository (where `.secrets` and `.github/copilot-instructions.json` are), and use the required `--repo` option to tell the agent where your project's repository is:

```bash
cd <path-to-assignment-repository>
source .venv/bin/activate
python3 src/issue_resolver.py --repo <path-to-your-repository>
```

Add `--verbose` (or `-v`) to also see every git command, GitHub API call, and the full prompt sent to Copilot.

## Work Out Which Repository

The agent checks that the folder given with `--repo` is a git repository. The `get_repo_slug()` function then reads the repository's `origin` remote URL and extracts its `owner/repo` name on GitHub.

## Load the GitHub Token

The agent reads `GITHUB_TOKEN` from the `.secrets` file in the current folder (the folder you ran the agent from). If that folder is inside your project's repository, the agent stops: there, the token could be committed, and Copilot could read it with a shell command such as `cat .secrets` (Copilot's permission rules for files do not cover shell commands).

## Pick the Oldest Open Issue

The agent then uses the GitHub API to list open issues sorted by creation date, oldest first, skipping pull requests (GitHub returns them from the same endpoint). This means that issues are resolved in the order you created them. If there are no open issues, the agent stops.

## Create a Fix Branch from Dev

The agent creates a branch named `issue-<n>-fix` (where `<n>` is the issue number) from the latest `origin/dev` and switches to it.

## Ask Copilot to Fix the Issue

The agent sends Copilot a prompt containing the contents of the `.github/copilot-instructions.json` file in the current folder (the folder you ran the agent from) followed by the issue number, title, and body. The prompt asks for the minimal change needed and tells Copilot not to commit or push.

Copilot runs non-interactively, so it cannot ask you for permission: every action it is not explicitly allowed to take is denied automatically. The `COPILOT_PERMISSIONS` list in the agent sets what it may do:

* **Allowed:** reading and editing files, read-only shell commands (e.g., `ls`, `cat`, `grep`), and running the tests with `pytest`.
* **Denied:** `git` and `gh` (the agent does that itself), `pip` (no package installs), `curl` and `wget` (no network access), opening `.secrets` with Copilot's file tools, and editing `.github/copilot-instructions.json` or `app/static/style.css`. Any other command that is not read-only is also denied.

Because the agent always runs from outside the project, `.secrets` is outside the folder Copilot works in. Copilot can only access files in its working folder, so it cannot read your token.

Copilot's output is shown as it works, so you can follow what it is doing. Test runs do not leave `.pytest_cache` or `__pycache__` folders behind, so they are not committed.

## Check for Changes

If Copilot did not change any files, the agent switches back to your original branch, deletes the fix branch, and stops.

## Commit and Push

The agent adds all changed files to the fix branch, commits them with the message `Fix #<n>: <issue title>`, and pushes the branch to GitHub.

## Open a Pull Request

The agent opens a pull request from the fix branch into `dev`. The pull request description includes `Closes #<n>`, so GitHub closes the issue automatically when the pull request is merged. Finally, the agent comments on the issue with a link to the pull request.

The agent never merges the pull request. Reviewing and merging it is your job.

---
name: kaggle-cli
description: Use the Kaggle CLI to install and authenticate the kaggle package, inspect command groups, download competition or dataset files, submit predictions, and work with Kaggle datasets, kernels, models, forums, benchmarks, and configuration.
compatibility: Requires Python 3.11+, pip, network access to Kaggle, and a Kaggle account with API credentials.
---

# Kaggle CLI

## Use This Skill When

- The user mentions Kaggle CLI, `kaggle`, Kaggle API credentials, Kaggle competitions, datasets, kernels, models, benchmarks, or submissions.
- The task requires downloading Kaggle data, creating a competition submission, checking CLI authentication, or choosing the right Kaggle command group.
- The user needs help installing, configuring, or troubleshooting the official `kaggle` package.

## Source

Based on the official Kaggle CLI documentation README:
https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md

## Setup Checklist

1. Confirm Python 3.11+ and `pip` are available.
2. Install the CLI with:

```sh
pip install kaggle
```

3. If `kaggle` is not found after installation, check that Python script directories are on `PATH`.
   - Linux user installs commonly use `~/.local/bin`.
   - Windows installs commonly use `$PYTHON_HOME/Scripts`.

4. Check available commands with:

```sh
kaggle --help
```

## Authentication

Prefer the least intrusive auth method that fits the environment. Never print, commit, or expose Kaggle tokens.

Use one of these official methods:

1. OAuth browser flow:

```sh
kaggle auth login
```

2. Environment variable:

```sh
export KAGGLE_API_TOKEN=xxxxxxxxxxxxxx
```

3. API token file:

```text
~/.kaggle/access_token
```

4. Legacy API credentials file:

```text
~/.kaggle/kaggle.json
```

Tokens come from the Kaggle account API settings page:
https://www.kaggle.com/settings/api

## Command Group Routing

Use `kaggle --help` first, then route work to the relevant command group:

- `competitions`: Manage and participate in Kaggle competitions.
- `datasets`: Search, download, create, and manage Kaggle datasets.
- `forums`: Browse and read Kaggle discussion forums.
- `kernels`: Work with Kaggle notebooks and scripts.
- `models`: Manage Kaggle Models.
- `model variations`: Manage variations of Kaggle Models.
- `model variation versions`: Manage versions of Kaggle Model Variations.
- `benchmarks`: Define evaluation tasks, run them against LLM models, and download results.
- `configuration`: Configure the Kaggle CLI.

For subcommand syntax, run:

```sh
kaggle <command-group> --help
```

## Competition Workflow

When preparing a competition submission:

1. Identify the competition slug and inspect competition help:

```sh
kaggle competitions --help
```

2. Download or refresh competition data using the appropriate `competitions` subcommand.
3. Generate the submission file in the exact format required by the competition.
4. Submit with the appropriate `competitions` submission subcommand.
5. Check the submission status and score after upload.

Keep generated submission files, downloaded datasets, and credentials out of commits unless the repository explicitly tracks those artifacts.

## Dataset Workflow

When working with Kaggle datasets:

1. Use the `datasets` command group for search, download, create, and management tasks.
2. Inspect exact syntax before running mutating operations:

```sh
kaggle datasets --help
```

3. For large downloads, confirm the destination directory and available disk space first.
4. Keep raw downloaded data out of source control unless the repository is designed to version it.

## Safety Rules

- Do not create or commit `kaggle.json`, `access_token`, `.env`, or pasted token values.
- Prefer environment variables or user-local credential files for authentication.
- Before running upload, create, submit, or other mutating commands, confirm the target competition, dataset, model, or benchmark.
- Use `--help` output from the installed CLI as the source of truth when command syntax differs from examples or memory.

# Electronic Tariff File

## Dependency Management

We use `pip-tools` to manage Python dependencies in a reliable and reproducible way. Flexible dependency specifications are declared in `.in` files, and fully pinned `.txt` lock files are automatically generated and used during runtime.

Each time the workflow runs, it compiles the `.txt` files with the latest compatible versions, ensuring up-to-date environments without manual intervention.

### How it works

1. Define top-level dependencies in `requirements.in` and `requirements_dev.in` using loose version specs (e.g., `requests`, `requests>=2.25.0`).
2. Run `pip-compile` to resolve and pin all dependencies into `requirements.txt` and `requirements_dev.txt`.
3. Use `pip-sync` to install exactly what’s listed in the `.txt` files—no more, no less.

To update dependencies:

```bash
pip-compile --upgrade --output-file=requirements.txt requirements.in
pip-compile --upgrade --output-file=requirements_dev.txt requirements_dev.in
pip-sync requirements.txt requirements_dev.txt
```

## Getting started for local development

```bash
python -m venv venv  # Create isolated Python environment
source venv/bin/activate  # Activate environment

# First time setup
pip install pip-tools  # Install dependency management tools
pip-compile requirements.in  # Generate requirements.txt
pip-compile requirements_dev.in  # Generate requirements_dev.txt
pip-sync requirements.txt requirements_dev.txt  # Install all dependencies
```

## Usage

### To create a new file in ICL VME format

`python create.py uk`

`python create.py uk 4 5`

#### Arguments

- argument 1 is the scope [uk|xi],
- argument 2 is the date, in format yyyy-mm-dd (optional). If omitted, then the current date will be used

#### Examples

To create a data file for the UK for a specific date (21st July 23)

`python create.py uk 2023-07-21`

To create a data file for XI for today

`python create.py xi`

### To parse an existing electronic Tariff file:

`python parse.py`

## Pre-commit

Pre-commit hooks are set up for linting and security scanning.

To install:
`pre-commit install`

To run all hooks manually:
`pre-commit run --all-files`

## Secrets

Secrets are managed via AWS Secrets Manager. They are automatically fetched during CI runs using GitHub Actions.

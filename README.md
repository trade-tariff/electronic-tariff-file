# Electronic Tariff File

This Python application creates Electronic Tariff files in ICL VME format for
UK and Northern Ireland data. It also parses existing files. Generation reads a
tariff database and can publish outputs and send notifications; it is not just a
local format converter.

Use Python 3, the PostgreSQL client and an approved local tariff dataset. See
[env.sample](env.sample) for configuration names and
[CI configuration](.github/workflows/ci.yml) for the integration environment.
Keep credentials and database dumps outside Git. Check output destinations before
running a generation command against shared services.

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

#### Arguments

- argument 1 is the scope [uk|xi],
- argument 2 is the date, in format yyyy-mm-dd (optional). If omitted, then the current date will be used

#### Examples

To create a data file for the UK for a specific date (21st July 23)

`python create.py uk 2023-07-21`

To create a data file for XI for today

`python create.py xi`

### Parse an existing Electronic Tariff file

`python parse.py`

## Pre-commit

Pre-commit hooks are set up for linting and security scanning.

To install:
`pre-commit install`

To run all hooks manually:
`pre-commit run --all-files`

## Secrets

CI obtains secrets through AWS Secrets Manager. A local checkout does not receive
those secrets automatically. Use approved development access and local configuration;
do not copy secrets into the tracked sample file.

## Checks and contributions

Run the configured pre-commit checks for source and documentation changes.
The CI integration restores a database dump and runs the generator; it needs
privileged access and is not an offline unit test. Review its target and output
settings before triggering it.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the fork workflow, review process and
private security reporting.

## Licence

The code and associated documentation use the [MIT licence](LICENCE.md), with
Crown copyright (HM Revenue & Customs). Input data and generated reports retain
their applicable data terms.

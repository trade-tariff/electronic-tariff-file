# Electronic Tariff File

## Implementation steps

- Create and activate a virtual environment, e.g.

  `python -m venv venv/`

  `source venv/bin/activate`

- Install dependencies

  `pip install pip-tools`

  `pip-sync requirements.txt requirements_dev.txt`

- Alternatively, if you're not using pip-sync, you can still use:

`pip install -r requirements.txt -r requirements_dev.txt`

### Dependency Management

Dependencies are managed using pip-tools.

**Adding dependencies**
- Add new packages to requirements.in (runtime dependencies) or requirements_dev.in (dev-only).

- Then recompile the locked .txt files:

`pip-compile --generate-hashes --output-file=requirements.txt requirements.in`

`pip-compile --generate-hashes --output-file=requirements_dev.txt requirements_dev.in`

This ensures all versions are pinned and avoids conflicts.

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

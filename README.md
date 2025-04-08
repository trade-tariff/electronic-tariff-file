# Electronic Tariff File

## Implementation steps

- Create and activate a virtual environment, e.g.

  `python -m venv venv/`

  `source venv/bin/activate`

- Install necessary Python modules via `pip install -r requirements.txt`

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

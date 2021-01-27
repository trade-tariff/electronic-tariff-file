# Electronic Tariff File

## Implementation steps

- Create and activate a virtual environment, e.g.

  `python3 -m venv venv/`
  `source venv/bin/activate`

- Install necessary Python modules 

  - autopep8==1.5.4
  - psycopg2==2.8.6
  - pycodestyle==2.6.0
  - python-dotenv==0.15.0
  - toml==0.10.2

  via `pip3 install -r requirements.txt`

## Usage

### To parse an existing electronic Tariff file:
`python3 parse.py`

### To create a new file in ICL VME format
`python3 create_icl_vme.py`

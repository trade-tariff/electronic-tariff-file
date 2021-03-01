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
`
python3 create.py
python3 create.py 1 2
`

### Rough numbers of commodities

0 = 3233
1 = 1506
2 = 5550
3 = 2126
4 = 1205
5 = 1461
6 = 1494
7 = 2486
8 = 4398
9 = 1149

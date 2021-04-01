# Electronic Tariff File

## Implementation steps

- Create and activate a virtual environment, e.g.

  `python3 -m venv venv/`
  `source venv/bin/activate`

- Install necessary Python modules 

  - autopep8==1.5.4
  - boto3==1.17.29
  - botocore==1.20.29
  - cffi==1.14.4
  - jmespath==0.10.0
  - multivolumefile==0.1.2
  - pathlib2==2.3.5
  - ppmd-cffi==0.3.2
  - psycopg2==2.8.6
  - py7zr==0.12.0
  - pycodestyle==2.6.0
  - pycparser==2.20
  - pycryptodome==3.9.9
  - python-dateutil==2.8.1
  - python-dotenv==0.15.0
  - s3transfer==0.3.4
  - six==1.15.0
  - texttable==1.6.3
  - toml==0.10.2
  - urllib3==1.26.4
  - zstandard==0.15.1

  via `pip3 install -r requirements.txt`

## Usage

### To parse an existing electronic Tariff file:
`python3 parse.py`

### To create a new file in ICL VME format
`
python3 create.py uk
python3 create.py uk 1 2` where argument 1 is the scope [uk|xi], argument 2 is the start index (1st digit of comm code) and argument 3 is the end index  (1st digit of comm code); arguments 2 and 3 are optional.

### To delete files from AWS
`
python3 aws_delete.py [pattern]
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

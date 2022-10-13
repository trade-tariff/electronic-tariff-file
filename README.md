# Electronic Tariff File

## Implementation steps

- Create and activate a virtual environment, e.g.

  `python3 -m venv venv/`

  `source venv/bin/activate`

- Install necessary Python modules via `pip3 install -r requirements.txt`

## Usage

### To parse an existing electronic Tariff file:
`python3 parse.py`

### To create a new file in ICL VME format

`python3 create.py uk`

`python3 create.py uk 4 5` 

#### Arguments
- argument 1 is the scope [uk|xi],
- argument 2 is the start index (1st digit of comm code)
- and argument 3 is the end index  (1st digit of comm code); arguments 2 and 3 are optional.

`python3 create.py uk 0 10 2022-07-21 ` where
`python3 create.py uk 0 10 2022-10-06` where

#### Arguments
- argument 1 is the scope [uk|xi],
- argument 2 is the start index (1st digit of comm code)
- and argument 3 is the end index  (1st digit of comm code); arguments 2 and 3 are optional.
- argument 4 is the date to create the data for

### To delete files from AWS

`python3 aws_delete.py [pattern]`

### Rough numbers of commodities

- 0 = 3233
- 1 = 1506
- 2 = 5550
- 3 = 2126
- 4 = 1205
- 5 = 1461
- 6 = 1494
- 7 = 2486
- 8 = 4398
- 9 = 1149

# New

`python3 generate_code_list.py uk`

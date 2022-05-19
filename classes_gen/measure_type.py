import sys
import classes.globals as g
from classes_gen.database import Database
from classes.functions import functions as f
from classes.enums import CommonString


class MeasureType(object):
    def __init__(self, taric_measure_type=None, measure_group_code=None, measure_type_code=None, tax_type_code=None):
        self.taric_measure_type = taric_measure_type
        self.measure_group_code = measure_group_code
        self.measure_type_code = measure_type_code
        self.tax_type_code = tax_type_code


class MeasureType2(object):
    def get_csv_string(self):
        s = ""
        s += CommonString.quote_char + f.null_to_string(self.measure_type_id) + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + f.null_to_string(self.description) + CommonString.quote_char
        s += CommonString.line_feed
        self.csv_string = s

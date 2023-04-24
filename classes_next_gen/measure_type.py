from classes_next_gen.functions import functions as f
from classes_next_gen.enums import CommonString


class MeasureType(object):
    def __init__(self, taric_measure_type=None, measure_group_code=None, measure_type_code=None, tax_type_code=None):
        self.taric_measure_type = taric_measure_type
        self.measure_group_code = measure_group_code
        self.measure_type_code = measure_type_code
        self.tax_type_code = tax_type_code
        self.certificate_code = ""

        self.split_taric_measure_type()

    def split_taric_measure_type(self):
        if "|" in self.taric_measure_type:
            tmp = self.taric_measure_type.split("|")
            self.taric_measure_type = tmp[0]
            self.certificate_code = tmp[1]


class MeasureType2(object):
    def get_csv_string(self):
        s = ""
        s += CommonString.quote_char + f.null_to_string(self.measure_type_id) + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + f.null_to_string(self.description) + CommonString.quote_char
        s += CommonString.line_feed
        self.csv_string = s

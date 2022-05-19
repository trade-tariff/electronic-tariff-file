import classes.globals as g
from classes.functions import functions as f
from classes.enums import CommonString


class AdditionalCode(object):
    def get_csv_string(self):
        s = ""
        s += CommonString.quote_char + f.null_to_string(self.code) + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + f.null_to_string(self.description) + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + f.null_to_string(self.validity_start_date) + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + f.null_to_string(self.validity_end_date) + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + f.null_to_string(self.additional_code_type_description) + CommonString.quote_char
        s += CommonString.line_feed
        self.csv_string = s

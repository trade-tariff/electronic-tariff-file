from classes.functions import functions as f
from classes.enums import CommonString

class Certificate(object):
    def __init__(self):
        pass
    
    def get_certificate_csv_string(self):
        self.format_description_for_csv()
        s = ""
        s += CommonString.quote_char + self.code + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + self.description + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + self.validity_start_date.strftime("%Y-%m-%d") + CommonString.quote_char + CommonString.comma
        if self.validity_end_date is None:
            s +=  CommonString.comma
        else:
            s += CommonString.quote_char + self.validity_end_date.strftime("%Y-%m-%d") + CommonString.quote_char
        s += CommonString.line_feed
        self.certificate_csv_string = s

    def format_description_for_csv(self):
        self.description = self.description.replace('"', "'")
        self.description = self.description.replace('\n', " ")
        self.description = self.description.replace('\r', " ")
        self.description = self.description.replace('  ', " ")

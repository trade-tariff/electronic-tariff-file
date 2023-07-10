from datetime import datetime

from classes.functions import functions as f
from classes.enums import CommonString


class QuotaDefinition(object):
    def __init__(self):
        self.exclusions = ""
        self.commodities = ""

    def get_csv_string(self):
        format = "%Y-%m-%d"
        self.validity_start_date_string = self.validity_start_date.strftime(format)
        if self.validity_end_date is None:
            self.validity_end_date_string = ""
        else:
            self.validity_end_date_string = self.validity_end_date.strftime(format)
        s = ""
        s += CommonString.quote_char + self.quota_order_number_id + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + self.validity_start_date_string + CommonString.quote_char + CommonString.comma
        if self.validity_end_date is None:
            s += CommonString.comma
        else:
            s += CommonString.quote_char + self.validity_end_date_string + CommonString.quote_char + CommonString.comma
        s += f.null_to_string(self.initial_volume) + CommonString.comma
        s += CommonString.quote_char + f.null_to_string(self.unit) + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + f.null_to_string(self.critical_state) + CommonString.quote_char + CommonString.comma
        s += f.null_to_string(self.critical_threshold) + CommonString.comma
        s += CommonString.quote_char + self.quota_type + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + self.origins + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + self.exclusions + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + self.commodities + CommonString.quote_char
        s += CommonString.line_feed
        self.csv_string = s


class QuotaExclusion(object):
    def __init__(self):
        pass


class QuotaCommodity(object):
    def __init__(self):
        pass

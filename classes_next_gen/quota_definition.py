from classes_next_gen.functions import functions as f
from classes_next_gen.enums import CommonString


class QuotaDefinition(object):
    def __init__(self):
        self.exclusions = ""
        self.commodities = ""

    def get_csv_string(self):
        s = ""
        s += CommonString.quote_char + self.quota_order_number_id + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + f.YYYY_MM_DD(self.validity_start_date) + CommonString.quote_char + CommonString.comma
        if self.validity_end_date is None:
            s += CommonString.comma
        else:
            s += CommonString.quote_char + f.YYYY_MM_DD(self.validity_end_date) + CommonString.quote_char + CommonString.comma
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

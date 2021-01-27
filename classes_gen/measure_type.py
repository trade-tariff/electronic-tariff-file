from classes.functions import functions as f
from classes.enums import CommonString

class MeasureType(object):
    def __init__(self, taric_measure_type, measure_group_code, measure_type_code):
        self.taric_measure_type = taric_measure_type
        self.measure_group_code = measure_group_code
        if measure_type_code == "":
            self.measure_type_code = taric_measure_type
        else:
            self.measure_type_code = measure_type_code

import csv
import os
import sys
import classes.globals as g
from classes.additional_code import AdditionalCode


class AdditionalCodeParser(object):
    def __init__(self):
        pass

    def parse(self):
        self.additional_codes = []
        self.filename = os.path.join(g.app.data_in_folder, "additional_codes_only.txt")
        file = open(self.filename, "r")
        for line in file:
            additional_code = AdditionalCode(line)
            self.additional_codes.append(additional_code.__dict__)

    def create_csv(self):
        csv_file = os.path.join(g.app.data_out_folder, "additional_codes.csv")
        csv_columns = [
            'RECORD_TYPE', 'EC_SUPP_COUNT', 'CODE_STRING', 'line']
        
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for additional_code in self.additional_codes:
                writer.writerow(additional_code)

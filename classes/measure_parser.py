import csv
import os
import sys
import classes.globals as g
from classes.measure import Measure


class MeasureParser(object):
    def __init__(self, which):
        if which == "ME":
            self.filename = os.path.join(g.app.data_in_folder, "measures_only.txt")
            self.csv_file = os.path.join(g.app.data_out_folder, "measures.csv")
        else:
            self.filename = os.path.join(g.app.data_in_folder, "measure_exceptions_only.txt")
            self.csv_file = os.path.join(g.app.data_out_folder, "measure_exceptions.csv")
        pass

    def parse(self):
        self.measures = []
        file = open(self.filename, "r")
        for line in file:
            measure = Measure(line)
            self.measures.append(measure.__dict__)

    def create_csv(self):
        csv_columns = [
            'RECORD_TYPE', 'MEASURE_GROUP_CODE', 'MEASURE_TYPE_CODE', 'TAX_TYPE_CODE',
            'TARIFF_MEASURE_EDATE', 'TARIFF_MEASURE_ETIME', 'TARIFF_MEASURE_LDATE', 'TARIFF_MEASURE_LTIME',
            'ORIGIN_COUNTRY_CODE', 'ORIGIN_COUNTRY_GROUP_CODE', 'ORIGIN_ADD_CHARGE_TYPE', 'DESTINATION_COUNTRY_CODE',
            'DESTINATION_CTY_GRP_CODE', 'DESTINATION_ADD_CH_TYPE', 'RATE_1', 'RATE_2', 'RATE_3', 'RATE_4', 'RATE_5', 'DUTY_TYPE',
            'CMDTY_MEASURE_EX_HEAD_IND', 'FREE_CIRC_DOTI_REQD_IND', 'QUOTA_NO', 'QUOTA_CODE_UK',
            'QUOTA_UNIT_OF_QUANTITY_CODE', 'MEASURE_AMENDMENT_IND', 'line']
               
        with open(self.csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for measure in self.measures:
                writer.writerow(measure)

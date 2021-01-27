import csv
import os
import sys
import classes.globals as g
from classes.commodity import Commodity


class CommodityParser(object):
    def __init__(self):
        pass

    def parse(self):
        self.commodities = []
        self.filename = os.path.join(g.app.data_in_folder, "commodities_only.txt")
        file = open(self.filename, "r")
        for line in file:
            commodity = Commodity(line)
            self.commodities.append(commodity.__dict__)

    def create_csv(self):
        csv_file = os.path.join(g.app.data_out_folder, "commodities.csv")
        csv_columns = [
            'RECORD_TYPE', 'COMMODITY_CODE', 'COMMODITY_EDATE', 'COMMODITY_ETIME',
            'COMMODITY_LDATE', 'COMMODITY_LTIME', 'EC_SUPP_CODE_IND', 'END_OF_SEASON_DATE', 'START_OF_SEASON_DATE',
            'SPV_CODE', 'COMMODITY_TYPE', 'WAREHOUSE_COMMODITY_IND', 'COMMODITY_END_USE_ALLWD',
            'COMMODITY_IMP_EXP_USE', 'COMMODITY_AMEND_IND', 'COMM_DECLARATION_UNIT_NO',
            'UNIT_OF_QUANTITY', 'ALPHA_SIZE', 'ALPHA_TEXT', 'line']

        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for commodity in self.commodities:
                writer.writerow(commodity)


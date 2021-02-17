import csv
import os
import json
import sys
import classes.globals as g
from classes.commodity import Commodity


class CommodityParser(object):
    def __init__(self):
        pass

    def parse(self):
        self.commodities = []
        self.filename = os.path.join(
            g.app.data_in_folder, "commodities_only.txt")
        file = open(self.filename, "r")
        for line in file:
            commodity = Commodity(line)
            self.commodities.append(commodity.__dict__)

    def create_csv(self):
        csv_file = os.path.join(g.app.data_out_folder, "commodities.csv")
        # csv_columns = [
        #     'RECORD_TYPE', 'COMMODITY_CODE', 'COMMODITY_EDATE', 'COMMODITY_ETIME',
        #     'COMMODITY_LDATE', 'COMMODITY_LTIME', 'EC_SUPP_CODE_IND', 'END_OF_SEASON_DATE', 'START_OF_SEASON_DATE',
        #     'SPV_CODE', 'COMMODITY_TYPE', 'WAREHOUSE_COMMODITY_IND', 'COMMODITY_END_USE_ALLWD',
        #     'COMMODITY_IMP_EXP_USE', 'COMMODITY_AMEND_IND', 'COMM_DECLARATION_UNIT_NO',
        #     'UNIT_OF_QUANTITY', 'ALPHA_SIZE', 'ALPHA_TEXT', 'line']
        csv_columns = [
            'RECORD_TYPE', 'COMMODITY_CODE', 'COMMODITY_EDATE', 'COMMODITY_ETIME',
            'COMMODITY_LDATE', 'COMMODITY_LTIME', 'EC_SUPP_CODE_IND', 'END_OF_SEASON_DATE', 'START_OF_SEASON_DATE',
            'SPV_CODE', 'COMMODITY_TYPE', 'WAREHOUSE_COMMODITY_IND', 'COMMODITY_END_USE_ALLWD',
            'COMMODITY_IMP_EXP_USE', 'COMMODITY_AMEND_IND',
            'UNIT1', 'UNIT2', 'UNIT3', 'ALPHA_SIZE', 'ALPHA_TEXT', 'line']

        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for commodity in self.commodities:
                writer.writerow(commodity)

        self.write_supp_code_json()

    def write_supp_code_json(self):
        json_file = os.path.join(g.app.reference_folder, "supp_units.json")
        my_dict = {}
        for commodity in self.commodities:
            unit1 = commodity["UNIT1"]
            unit2 = commodity["UNIT2"]
            unit3 = commodity["UNIT3"]
            obj = SuppCodeList(unit1, unit2, unit3)
            my_dict[commodity["COMMODITY_CODE"]] = obj.__dict__

        my_json = json.dumps(my_dict, indent=4, sort_keys=False)
        f = open(json_file, "w+")
        f.write(my_json)
        f.close()


class SuppCodeList(object):
    def __init__(self, unit1, unit2, unit3):
        self.unit1 = unit1
        self.unit2 = unit2
        self.unit3 = unit3
        
        if self.unit1 == "1030":
            self.unit1 = "1023"
            self.unit2 = "1030"

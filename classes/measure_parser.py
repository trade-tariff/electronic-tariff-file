import csv
import os
import classes.globals as g


class MeasureParser(object):
    def __init__(self, prefix):
        self.prefix = prefix

    def parse(self):
        self.measures = []
        file = open(g.parsed_file, "r")
        for line in file:
            if line[0:2] == self.prefix:
                me = ParsedMeasure(line)
                self.measures.append(me.__dict__)

    def create_csv(self):
        csv_columns = [
            "RECORD_TYPE",
            "MEASURE_GROUP_CODE",
            "MEASURE_TYPE_CODE",
            "TAX_TYPE_CODE",
            "TARIFF_MEASURE_EDATE",
            "TARIFF_MEASURE_ETIME",
            "TARIFF_MEASURE_LDATE",
            "TARIFF_MEASURE_LTIME",
            "ORIGIN_COUNTRY_CODE",
            "ORIGIN_COUNTRY_GROUP_CODE",
            "ORIGIN_ADD_CHARGE_TYPE",
            "DESTINATION_COUNTRY_CODE",
            "DESTINATION_CTY_GRP_CODE",
            "DESTINATION_ADD_CH_TYPE",
            "RATE_1",
            "RATE_2",
            "RATE_3",
            "RATE_4",
            "RATE_5",
            "DUTY_TYPE",
            "CMDTY_MEASURE_EX_HEAD_IND",
            "FREE_CIRC_DOTI_REQD_IND",
            "QUOTA_NO",
            "QUOTA_CODE_UK",
            "QUOTA_UNIT_OF_QUANTITY_CODE",
            "MEASURE_AMENDMENT_IND",
            "line",
        ]

        if self.prefix == "ME":
            self.csv_file = os.path.join(g.parse_folder, "measures.csv")
        else:
            self.csv_file = os.path.join(g.parse_folder, "measure_exceptions.csv")

        with open(self.csv_file, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for measure in self.measures:
                writer.writerow(measure)


class ParsedMeasure(object):
    def __init__(self, line):
        self.line = line
        self.parse()

    def parse(self):
        self.RECORD_TYPE = self.line[0:2]
        self.MEASURE_GROUP_CODE = self.line[2:4]
        self.MEASURE_TYPE_CODE = self.line[4:7]
        self.TAX_TYPE_CODE = self.line[7:10]
        self.TARIFF_MEASURE_EDATE = self.line[10:18]
        self.TARIFF_MEASURE_ETIME = self.line[18:24]
        self.TARIFF_MEASURE_LDATE = self.line[24:32]
        self.TARIFF_MEASURE_LTIME = self.line[32:38]
        self.ORIGIN_COUNTRY_CODE = self.line[38:40]
        self.ORIGIN_COUNTRY_GROUP_CODE = self.line[40:44]
        self.ORIGIN_ADD_CHARGE_TYPE = self.line[44:45]
        self.DESTINATION_COUNTRY_CODE = self.line[45:47]
        self.DESTINATION_CTY_GRP_CODE = self.line[47:51]
        self.DESTINATION_ADD_CH_TYPE = self.line[51:52]

        self.RATE_1 = self.line[52:75]
        self.RATE_2 = self.line[75:98]
        self.RATE_3 = self.line[98:121]
        self.RATE_4 = self.line[121:144]
        self.RATE_5 = self.line[144:167]

        self.DUTY_TYPE = self.line[167:169]
        self.CMDTY_MEASURE_EX_HEAD_IND = self.line[169:170]
        self.FREE_CIRC_DOTI_REQD_IND = self.line[170:171]
        self.QUOTA_NO = self.line[171:177]
        self.QUOTA_CODE_UK = self.line[177:181]
        self.QUOTA_UNIT_OF_QUANTITY_CODE = self.line[181:184]
        self.MEASURE_AMENDMENT_IND = self.line[184:185]

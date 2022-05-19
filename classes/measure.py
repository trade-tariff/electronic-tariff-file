class Measure(object):
    def __init__(self, line, commodity=""):
        self.line = line
        self.commodity = commodity
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

        if self.commodity == "":
            self.line = ""

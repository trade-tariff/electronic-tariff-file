from classes.enums import CommonString

class Commodity(object):
    def __init__(self, line):
        self.line = line
        self.parse()

    def parse(self):
        self.RECORD_TYPE = self.line[0:2]
        self.COMMODITY_CODE = self.line[2:12]
        self.COMMODITY_EDATE = self.line[12:20]
        self.COMMODITY_ETIME = self.line[20:26]
        self.COMMODITY_LDATE = self.line[26:34]
        self.COMMODITY_LTIME = self.line[34:40]
        self.EC_SUPP_CODE_IND = self.line[40:41]
        self.END_OF_SEASON_DATE = self.line[41:47]
        self.START_OF_SEASON_DATE = self.line[47:53]
        self.SPV_CODE = self.line[53:60]
        self.COMMODITY_TYPE = self.line[60:61]
        self.WAREHOUSE_COMMODITY_IND = self.line[61:62]
        self.COMMODITY_END_USE_ALLWD = self.line[62:63]
        self.COMMODITY_IMP_EXP_USE = self.line[63:64]
        self.COMMODITY_AMEND_IND = self.line[64:65]
        self.UNIT1 = self.line[65:69]
        self.UNIT2 = self.line[69:73]
        self.UNIT3 = self.line[73:77]
        self.ALPHA_SIZE = self.line[77:81]
        self.ALPHA_TEXT = self.line[81:].rstrip()
        self.line = ""
        
        # f = open("spvs.txt", "a")
        
        # if self.SPV_CODE.strip() != "":
        #     f.write(self.COMMODITY_CODE + "," + self.SPV_CODE + "\n")
        # f.close()

from classes.functions import functions as f
from classes.enums import CommonString

class Commodity(object):
    def __init__(self):
        self.RECORD_TYPE = "CM"
        self.COMMODITY_CODE = ""
        self.COMMODITY_EDATE = ""
        self.COMMODITY_ETIME = "000000"
        self.COMMODITY_LDATE = ""
        self.COMMODITY_LTIME = "000000"
        self.EC_SUPP_CODE_IND = "I"
        self.END_OF_SEASON_DATE = "000000"
        self.START_OF_SEASON_DATE = "000000"
        self.SPV_CODE = "       "
        self.COMMODITY_TYPE = "0"
        self.WAREHOUSE_COMMODITY_IND = "N"
        self.COMMODITY_END_USE_ALLWD = "N"
        self.COMMODITY_IMP_EXP_USE = "0"
        self.COMMODITY_AMEND_IND = " "
        self.COMM_DECLARATION_UNIT_NO = "10"
        self.UNIT_OF_QUANTITY = "232"
        self.ALPHA_SIZE = ""
        self.ALPHA_TEXT = ""

        self.goods_nomenclature_sid = None
        self.productline_suffix = None
        self.description = ""
        self.number_indents = None
        self.leaf = None
        self.hierarchy = []
        self.hierarchy_string = ""
        
    def build_hierarchy_string(self):
        token = ""
        self.hierarchy.append(self)
        if len(self.hierarchy) > 0:
            for item in self.hierarchy:
                if item.significant_digits == 10:
                    token = "++++"
                else:
                    if item.number_indents == 0:
                        token = ""
                    elif item.number_indents == 1:
                        token = ":"
                    elif item.number_indents == 2:
                        token = ":*"
                    elif item.number_indents == 3:
                        token = ":**"
                    elif item.number_indents == 4:
                        token = ":***"
                    elif item.number_indents == 5:
                        token = ":****"
                self.hierarchy_string += token + item.description
            # self.hierarchy_string += self.description
            self.ALPHA_TEXT = self.hierarchy_string
        else:
            self.ALPHA_TEXT = self.description
        
        self.ALPHA_SIZE = str(len(self.ALPHA_TEXT)).zfill(11) 
            
        
    def create_extract_line(self):
        self.extract_line = self.RECORD_TYPE
        self.extract_line += self.COMMODITY_CODE
        self.extract_line += self.COMMODITY_EDATE
        self.extract_line += self.COMMODITY_ETIME
        self.extract_line += self.COMMODITY_LDATE
        self.extract_line += self.COMMODITY_LTIME
        self.extract_line += self.EC_SUPP_CODE_IND
        self.extract_line += self.END_OF_SEASON_DATE
        self.extract_line += self.START_OF_SEASON_DATE
        self.extract_line += self.SPV_CODE
        self.extract_line += self.COMMODITY_TYPE
        self.extract_line += self.WAREHOUSE_COMMODITY_IND
        self.extract_line += self.COMMODITY_END_USE_ALLWD
        self.extract_line += self.COMMODITY_IMP_EXP_USE
        self.extract_line += self.COMMODITY_AMEND_IND
        self.extract_line += self.COMM_DECLARATION_UNIT_NO
        self.extract_line += self.UNIT_OF_QUANTITY
        self.extract_line += self.ALPHA_SIZE
        self.extract_line += self.ALPHA_TEXT

        self.extract_line += CommonString.line_feed
        
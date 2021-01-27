from classes.functions import functions as f
from classes.enums import CommonString

class Measure(object):
    def __init__(self):
        self.extract_line = None

        self.RECORD_TYPE = "ME" # or MX
        self.MEASURE_GROUP_CODE = "  "
        self.MEASURE_TYPE_CODE = "YYY"
        self.TAX_TYPE_CODE = "XXX"
        self.TARIFF_MEASURE_EDATE = "20210101" # validity_start_date
        self.TARIFF_MEASURE_ETIME = "000000"
        self.TARIFF_MEASURE_LDATE = "00000000" # validity_end_date
        self.TARIFF_MEASURE_LTIME = "000000"
        self.ORIGIN_COUNTRY_CODE = "  "
        self.ORIGIN_COUNTRY_GROUP_CODE = "    "
        self.ORIGIN_ADD_CHARGE_TYPE = "X"
        self.DESTINATION_COUNTRY_CODE = "AA"
        self.DESTINATION_CTY_GRP_CODE = "A999"
        self.DESTINATION_ADD_CH_TYPE = "X"
        self.UNIT_OF_QUANTITY_CODE = "111"
        self.QUANTITY_CODE = "222"
        self.UNIT_ACCOUNT = "1"
        self.SPECIFIC_RATE = "0000000000"
        self.AD_VALOREM_RATE = "1111111111"
        self.DUTY_TYPE = "22222"
        self.CMDTY_MEASURE_EX_HEAD_IND = "N"
        self.FREE_CIRC_DOTI_REQD_IND = "X"
        self.QUOTA_NO = "000000"
        self.QUOTA_CODE_UK = "1111"
        self.QUOTA_UNIT_OF_QUANTITY_CODE = "222"
        self.MEASURE_AMENDMENT_IND = "X"
        
        # Taric / CDS data
        self.measure_type_id = None
        
    def expand_raw_data(self, measure_types):
        self.resolve_geography()
        self.resolve_dates()
        self.lookup_measure_types(measure_types)
        
    def resolve_dates(self):
        self.TARIFF_MEASURE_EDATE = f.YYYYMMDD(self.validity_start_date)
        pass
        
    def resolve_geography(self):
        if len(self.geographical_area_id) == 2:
            self.ORIGIN_COUNTRY_CODE = self.geographical_area_id
            self.ORIGIN_COUNTRY_GROUP_CODE = "    "
        else:
            self.ORIGIN_COUNTRY_CODE = "  "
            self.ORIGIN_COUNTRY_GROUP_CODE = self.geographical_area_id

    def lookup_measure_types(self, measure_types):
        # This is a temp thing for testing only
        self.MEASURE_TYPE_CODE = self.measure_type_id

        for measure_type in measure_types:
            if measure_type.taric_measure_type == self.measure_type_id:
                self.MEASURE_GROUP_CODE = measure_type.measure_group_code
                self.MEASURE_TYPE_CODE = measure_type.measure_type_code
                break
        
                

    def create_extract_line(self):
        self.extract_line = self.RECORD_TYPE
        self.extract_line += self.MEASURE_GROUP_CODE
        self.extract_line += self.MEASURE_TYPE_CODE
        self.extract_line += self.TAX_TYPE_CODE
        self.extract_line += self.TARIFF_MEASURE_EDATE
        self.extract_line += self.TARIFF_MEASURE_ETIME
        self.extract_line += self.TARIFF_MEASURE_LDATE
        self.extract_line += self.TARIFF_MEASURE_LTIME
        self.extract_line += self.ORIGIN_COUNTRY_CODE
        self.extract_line += self.ORIGIN_COUNTRY_GROUP_CODE
        self.extract_line += self.ORIGIN_ADD_CHARGE_TYPE
        self.extract_line += self.DESTINATION_COUNTRY_CODE
        self.extract_line += self.DESTINATION_CTY_GRP_CODE
        self.extract_line += self.DESTINATION_ADD_CH_TYPE
        self.extract_line += self.UNIT_OF_QUANTITY_CODE
        self.extract_line += self.QUANTITY_CODE
        self.extract_line += self.UNIT_ACCOUNT
        self.extract_line += self.SPECIFIC_RATE
        self.extract_line += self.AD_VALOREM_RATE
        self.extract_line += self.DUTY_TYPE
        self.extract_line += self.CMDTY_MEASURE_EX_HEAD_IND
        self.extract_line += self.FREE_CIRC_DOTI_REQD_IND
        self.extract_line += self.QUOTA_NO
        self.extract_line += self.QUOTA_CODE_UK
        self.extract_line += self.QUOTA_UNIT_OF_QUANTITY_CODE
        self.extract_line += self.MEASURE_AMENDMENT_IND
        self.extract_line += "   " + self.goods_nomenclature_item_id
        self.extract_line += CommonString.line_feed

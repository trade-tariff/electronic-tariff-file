from classes.functions import functions as f
from classes.enums import CommonString

class Measure(object):
    def __init__(self):
        self.extract_line = None

        self.RECORD_TYPE = "ME" # or MX
        self.MEASURE_GROUP_CODE = "  "
        self.MEASURE_TYPE_CODE = "   "
        self.TAX_TYPE_CODE = "!!!"
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
        self.DUTY_TYPE = "00"
        self.CMDTY_MEASURE_EX_HEAD_IND = "N"
        self.FREE_CIRC_DOTI_REQD_IND = "X"
        self.QUOTA_NO = "000000"
        self.QUOTA_CODE_UK = "0000" # Always four zeroes
        self.QUOTA_UNIT_OF_QUANTITY_CODE = "222"
        self.MEASURE_AMENDMENT_IND = "A"
        
        # Taric / CDS data
        self.measure_type_id = None
        self.measure_components = []
        self.measure_excluded_geographical_areas = []
        
    def expand_raw_data(self, measure_types, geographical_areas):
        self.resolve_geography(geographical_areas)
        self.resolve_dates()
        self.lookup_measure_types(measure_types)

        if self.ordernumber != "" and self.ordernumber is not None:
            self.QUOTA_NO = self.ordernumber
            
        self.CMDTY_MEASURE_EX_HEAD_IND = ("0" * 85) + self.CMDTY_MEASURE_EX_HEAD_IND
        
    def resolve_dates(self):
        self.TARIFF_MEASURE_EDATE = f.YYYYMMDD(self.validity_start_date)

    def get_import_export(self):
        if self.trade_movement_code == 0:
            self.is_import = True
            self.is_export = False
        if self.trade_movement_code == 1:
            self.is_import = False
            self.is_export = True
        else:
            self.is_import = True
            self.is_export = True
    
    def create_measure_duties(self):
        # This is intended to resolve the following
        # self.SPECIFIC_RATE = "0000000000"
        # self.AD_VALOREM_RATE = "1111111111"
        # self.DUTY_TYPE = "22"
        if self.measure_component_applicable_code == 2 or self.measure_type_series_id in ("A", "B"):
            self.DUTY_TYPE = "00"
        else:
            valid_duty_expressions = ['01', '04', '19', '20']

            self.has_specific = False
            self.has_advalorem = False
            
            for mc in self.measure_components:
                if mc.duty_expression_id in valid_duty_expressions:
                    if mc.monetary_unit_code is None:
                        self.has_advalorem = True
                    else:
                        self.has_specific = True
                        
            if len(self.measure_components) == 1:
                if self.measure_components[0].duty_amount == 0:
                    # Free of all duties = type 22
                    self.DUTY_TYPE = "60"
                else:
                    if self.measure_components[0].monetary_unit_code is None:
                        # Just one component and it is specific
                        self.DUTY_TYPE = "01"
                    else:
                        # Just one component and it is ad valorem (but non-zero)
                        self.DUTY_TYPE = "10"
            elif len(self.measure_components) == 2:
                # print(str(self.measure_sid) + " on comm code " + self.goods_nomenclature_item_id + " has 2 components")
                mc0 = self.measure_components[0]
                mc1 = self.measure_components[1]
                if mc0.monetary_unit_code is None:
                    # These 2 options are for when the first of 2 components is ad valorem
                    if mc1.monetary_unit_code is None:
                        print("Two ad valorems - not expected")
                    else:
                        # Two components: ad valorem followed by a specific
                        self.DUTY_TYPE = "18"
                else:
                    # These 2 options are for when the first of 2 components is specific
                    if mc1.monetary_unit_code is None:
                        print("Specific plus ad valorem - not expected")
                    else:
                        # Two components: specific followed by a specific
                        self.DUTY_TYPE = "62"
            elif len(self.measure_components) > 2:
                # There are three commodity codes where there are three components on the MFN: when you open it to other measures, there are hundreds
                # 2009697100
                # 2009697900
                # 2009691100
                print(str(self.measure_sid) + " on comm code " + self.goods_nomenclature_item_id + " has > 2 components")
                
            c = "0305720056"
            if self.goods_nomenclature_item_id == c:
                print(self.DUTY_TYPE + " is the duty type for comm code " + c + " on measure type " + self.measure_type_id + " on country " + self.geographical_area_id + " on measure " + str(self.measure_sid))
                

    def resolve_geography(self, geographical_areas):
        if len(self.geographical_area_id) == 2:
            # Standard country or region code
            self.ORIGIN_COUNTRY_CODE = self.geographical_area_id
            self.ORIGIN_COUNTRY_GROUP_CODE = "    "
        else:
            # Country groups need to be looked up in the list of geographical areas
            self.ORIGIN_COUNTRY_CODE = "  "
            found = False
            for geographical_area in geographical_areas:
                if self.geographical_area_id == geographical_area.taric_area:
                    self.ORIGIN_COUNTRY_GROUP_CODE = geographical_area.chief_area
                    found = True
                    break
            if not found:
                self.ORIGIN_COUNTRY_GROUP_CODE = self.geographical_area_id 
                # self.ORIGIN_COUNTRY_GROUP_CODE = "***" + self.geographical_area_id + "***"

    def lookup_measure_types(self, measure_types):
        # This is a temp thing for testing only
        self.MEASURE_TYPE_CODE = self.measure_type_id

        if self.measure_type_id == "305":
            # All of the following are VAT
            self.MEASURE_GROUP_CODE = "VT"
            self.TAX_TYPE_CODE = "B00"
            if self.additional_code is None or self.additional_code == "":
                self.MEASURE_TYPE_CODE = "666"
            elif self.additional_code == "VATE":
                self.MEASURE_TYPE_CODE = "654"
            elif self.additional_code == "VATR":
                self.MEASURE_TYPE_CODE = "650"
            elif self.additional_code == "VATZ":
                self.MEASURE_TYPE_CODE = "673"

        elif self.measure_type_id == "306":
            # All of the following are excise
            self.MEASURE_GROUP_CODE = "EX"
            if self.additional_code == "X99A":
                self.MEASURE_TYPE_CODE = "EXA"
                self.TAX_TYPE_CODE = "990"
            elif self.additional_code == "X99B":
                self.MEASURE_TYPE_CODE = "EXB"
                self.TAX_TYPE_CODE = "990"
            elif self.additional_code == "X99C":
                self.MEASURE_TYPE_CODE = "EXC"
                self.TAX_TYPE_CODE = "990"
            elif self.additional_code == "X99D":
                self.MEASURE_TYPE_CODE = "EXD"
                self.TAX_TYPE_CODE = "990"
            else:
                self.MEASURE_TYPE_CODE = "600"
                self.TAX_TYPE_CODE = self.additional_code.replace("X", "")
                
        else:
            for measure_type in measure_types:
                if measure_type.taric_measure_type == self.measure_type_id:
                    self.MEASURE_GROUP_CODE = measure_type.measure_group_code
                    if measure_type.measure_type_code == "PRF":
                        if self.geographical_area_id in ('2005', '2029', '2027'):
                            self.MEASURE_TYPE_CODE = "101"
                        else:
                            self.MEASURE_TYPE_CODE = "100"
                    else:
                        self.MEASURE_TYPE_CODE = measure_type.measure_type_code
                    self.TAX_TYPE_CODE = measure_type.tax_type_code
                    break

    def create_extract_line(self):
        self.extract_line = self.RECORD_TYPE + CommonString.divider
        self.extract_line += self.MEASURE_GROUP_CODE + CommonString.divider
        self.extract_line += self.MEASURE_TYPE_CODE + CommonString.divider
        self.extract_line += self.TAX_TYPE_CODE + CommonString.divider
        self.extract_line += self.TARIFF_MEASURE_EDATE + CommonString.divider
        self.extract_line += self.TARIFF_MEASURE_ETIME + CommonString.divider
        self.extract_line += self.TARIFF_MEASURE_LDATE + CommonString.divider
        self.extract_line += self.TARIFF_MEASURE_LTIME + CommonString.divider
        self.extract_line += self.ORIGIN_COUNTRY_CODE + CommonString.divider
        self.extract_line += self.ORIGIN_COUNTRY_GROUP_CODE + CommonString.divider
        self.extract_line += self.ORIGIN_ADD_CHARGE_TYPE + CommonString.divider
        self.extract_line += self.DESTINATION_COUNTRY_CODE + CommonString.divider
        self.extract_line += self.DESTINATION_CTY_GRP_CODE + CommonString.divider
        self.extract_line += self.DESTINATION_ADD_CH_TYPE + CommonString.divider
        self.extract_line += self.UNIT_OF_QUANTITY_CODE + CommonString.divider
        self.extract_line += self.QUANTITY_CODE + CommonString.divider
        self.extract_line += self.UNIT_ACCOUNT + CommonString.divider
        self.extract_line += self.SPECIFIC_RATE + CommonString.divider
        self.extract_line += self.AD_VALOREM_RATE + CommonString.divider
        self.extract_line += self.DUTY_TYPE + CommonString.divider
        self.extract_line += self.CMDTY_MEASURE_EX_HEAD_IND + CommonString.divider
        self.extract_line += self.FREE_CIRC_DOTI_REQD_IND + CommonString.divider
        self.extract_line += self.QUOTA_NO + CommonString.divider
        self.extract_line += self.QUOTA_CODE_UK + CommonString.divider
        self.extract_line += self.QUOTA_UNIT_OF_QUANTITY_CODE + CommonString.divider
        self.extract_line += self.MEASURE_AMENDMENT_IND
        self.extract_line += "   " + self.goods_nomenclature_item_id
        self.extract_line += CommonString.line_feed

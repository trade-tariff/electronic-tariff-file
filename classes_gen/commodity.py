import sys

from classes.functions import functions as f
from classes.enums import CommonString
from classes_gen.supplementary_unit import SupplementaryUnit

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
        self.measures = []
        self.measures_inherited = []
        self.footnotes = []
        self.additional_codes = []
        
    def apply_commodity_inheritance(self):
        if self.leaf == "1":
            for commodity in self.hierarchy:
                for measure in commodity.measures:
                    self.measures_inherited.append(measure)
                    # print('%s gets measure %d from commodity %s' % (self.COMMODITY_CODE, measure.measure_sid, commodity.COMMODITY_CODE))
                
    def sort_inherited_measures(self):
        self.measures_inherited.sort(key=lambda x: x.geographical_area_id, reverse=False)
        self.measures_inherited.sort(key=lambda x: x.measure_type_id, reverse=False)
        pass
    
    def get_commodity_additional_codes(self):
        self.additional_codes = []
        for measure in self.measures_inherited:
            if measure.additional_code_type_id is not None:
                self.additional_codes.append(measure.additional_code)
                print("Assigning an additional code to commodity " + self.COMMODITY_CODE)
            
    def get_supplementary_units(self, supplementary_units_reference):
        self.get_supplementary_unit = None
        supp_types = ['109', '110', '111']
        found_quantity_code = False
        for measure in self.measures_inherited:
            if measure.measure_type_id in supp_types:
                measure_component = measure.measure_components[0]
                self.supplementary_unit = SupplementaryUnit()
                self.supplementary_unit.measurement_unit_code = measure_component.measurement_unit_code
                self.supplementary_unit.measurement_unit_qualifier_code = measure_component.measurement_unit_qualifier_code
                if self.supplementary_unit.measurement_unit_qualifier_code is None:
                    self.supplementary_unit.measurement_unit_qualifier_code = ""
                
                for item in supplementary_units_reference:
                    if self.supplementary_unit.measurement_unit_code == item.measurement_unit_code:
                        if self.supplementary_unit.measurement_unit_qualifier_code == item.measurement_unit_qualifier_code:
                            self.supplementary_unit.quantity_code = item.quantity_code
                            #print ("Found supp code on comm code " + self.COMMODITY_CODE + " with q code " + item.quantity_code)
                            found_quantity_code = True
                            break
                
                if found_quantity_code == False:
                    print ("Missing supp code on comm code " + self.COMMODITY_CODE)
                else:
                    break
                    

    def get_end_use(self):
        # There may be some other criteria that need to be considered here
        # At least temporarily, we are just checking to see if there is a 
        # 105 measure, and this signifies that the comm code is end use
        # The 105 may be inherited down
        self.is_end_use = False
        for measure in self.measures_inherited:
            if measure.measure_type_id == "105":
                self.is_end_use = True
                break
        if self.is_end_use:
            self.COMMODITY_END_USE_ALLWD = "Y"
            # print('Found an end use commodity code %s' % (self.COMMODITY_CODE))
        else:
            self.COMMODITY_END_USE_ALLWD = "N"

    def append_footnotes_to_description(self):
        if 1 > 0:
            if len(self.footnotes) > 0:
                for footnote in self.footnotes:
                    self.description += "<" + footnote.FOOTNOTE_NUMBER + ">"
    
    def build_hierarchy_string(self):
        # This function is not fully working - need to understand the logic for the Taric codes + n
        token = ""
        self.hierarchy.append(self)
        if len(self.hierarchy) > 0:
            for item in self.hierarchy:
                if item.significant_digits != 2:
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
            self.ALPHA_TEXT = self.hierarchy_string
        else:
            self.ALPHA_TEXT = self.description
        
        self.ALPHA_SIZE = str(len(self.ALPHA_TEXT)).zfill(11) 
            
    def create_extract_line(self):
        self.extract_line = self.RECORD_TYPE + CommonString.divider
        self.extract_line += self.COMMODITY_CODE + CommonString.divider
        self.extract_line += self.COMMODITY_EDATE + CommonString.divider
        self.extract_line += self.COMMODITY_ETIME + CommonString.divider
        self.extract_line += self.COMMODITY_LDATE + CommonString.divider
        self.extract_line += self.COMMODITY_LTIME + CommonString.divider
        self.extract_line += self.EC_SUPP_CODE_IND + CommonString.divider
        self.extract_line += self.END_OF_SEASON_DATE + CommonString.divider
        self.extract_line += self.START_OF_SEASON_DATE + CommonString.divider
        self.extract_line += self.SPV_CODE + CommonString.divider
        self.extract_line += self.COMMODITY_TYPE + CommonString.divider
        self.extract_line += self.WAREHOUSE_COMMODITY_IND + CommonString.divider
        self.extract_line += self.COMMODITY_END_USE_ALLWD + CommonString.divider
        self.extract_line += self.COMMODITY_IMP_EXP_USE + CommonString.divider
        self.extract_line += self.COMMODITY_AMEND_IND + CommonString.divider
        self.extract_line += self.COMM_DECLARATION_UNIT_NO + CommonString.divider
        self.extract_line += self.UNIT_OF_QUANTITY + CommonString.divider
        self.extract_line += self.ALPHA_SIZE + CommonString.divider
        self.extract_line += self.ALPHA_TEXT

        self.extract_line += CommonString.line_feed
        
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
        self.COMMODITY_TYPE = "0" # Set it determine_commodity_type
        self.WAREHOUSE_COMMODITY_IND = "N" # This is always set to "N"
        self.COMMODITY_END_USE_ALLWD = "N" # Basing this on the judgement call of 103 versus 105 duty
        self.COMMODITY_IMP_EXP_USE = "0" # Always zero
        self.COMMODITY_AMEND_IND = " " # An amendment indicator - has this changed since last time? 1st instance this will be set to A (I think)
        self.UNIT_OF_QUANTITY = "1023" + CommonString.unit_divider + "0000" + CommonString.unit_divider + "0000" # The applicable supplementary unit(s) - we're making this 12 digits long
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
        self.seasonal = False
        self.additional_code_string = ""
        
        self.determine_commodity_type()
        
    def determine_commodity_type(self):
        if self.leaf == "1":
            if self.significant_digits == 10:
                self.COMMODITY_TYPE = "2"
            else:
                self.COMMODITY_TYPE = "0"
        else:
            self.COMMODITY_TYPE = "1"
        
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
    
    def get_supplementary_units(self, supplementary_units_reference):
        self.get_supplementary_unit = None
        supp_types = ['109', '110', 'x111']
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
                    self.UNIT_OF_QUANTITY = "1023" + CommonString.unit_divider + "2" + self.supplementary_unit.quantity_code + CommonString.unit_divider + "0000"
                    break

    def apply_seasonal_rates(self, seasonal_rates):
        for seasonal_rate in seasonal_rates:
            for item in self.hierarchy:
                if item.COMMODITY_CODE == seasonal_rate.goods_nomenclature_item_id:
                    self.seasonal = True
                    self.END_OF_SEASON_DATE = seasonal_rate.to_date
                    self.START_OF_SEASON_DATE = seasonal_rate.from_date
                    break
            
    def get_additional_code_indicator(self):
        """
        CODE IMPORT          EXPORT
        E    Optional        Optional
        F    Optional        Not Applicable
        G    Not Applicable  Mandatory - there can't be any of these while there are few export measures
        H    Not Applicable  Optional
        I    Not Applicable  Not Applicable
        """
        self.additional_codes = []
        self.has_import_additional_codes = False
        self.has_export_additional_codes = False
        for measure in self.measures_inherited:
            if measure.additional_code_type_id is not None and measure.additional_code_type_id != "":
                if measure.additional_code_type_id not in ('V', 'X'):
                    self.additional_codes.append(measure.additional_code)
                    if measure.is_import:
                        self.has_import_additional_codes = True
                    if measure.is_export:
                        self.has_export_additional_codes = True
        
        if self.has_import_additional_codes:
            if self.has_export_additional_codes:
                self.EC_SUPP_CODE_IND = "E"
            else:
                self.EC_SUPP_CODE_IND = "F"
        elif self.has_export_additional_codes:
            self.EC_SUPP_CODE_IND = "H"
        else:
            self.EC_SUPP_CODE_IND = "I"
            
        self.get_additional_code_string()
        
    def get_additional_code_string(self):
        # CA000291409150
        self.additional_code_string = ""
        if len(self.additional_codes) > 0:
            self.additional_codes.sort()
            self.additional_code_string = "CA"
            self.additional_code_string += str(len(self.additional_codes)).rjust(4, "0")
            for additional_code in self.additional_codes:
                print("Ya")
                self.additional_code_string += additional_code

            print(self.additional_code_string)
            self.additional_code_string += CommonString.line_feed

    def get_spv(self, spvs):
        found = False
        for spv in spvs:
            if spv.goods_nomenclature_item_id == self.COMMODITY_CODE:
                found = True
                self.SPV_CODE = spv.spv_code
                break

        if not found:
            self.SPV_CODE = "       "
            
        # This is based on the fact that there are no Unit Price measures in the database
        self.SPV_CODE = "       "

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
        
        self.ALPHA_SIZE = str(len(self.ALPHA_TEXT)).zfill(4) 
            
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
        # self.extract_line += self.COMM_DECLARATION_UNIT_NO + CommonString.divider
        self.extract_line += self.UNIT_OF_QUANTITY + CommonString.divider
        self.extract_line += self.ALPHA_SIZE + CommonString.divider
        self.extract_line += self.ALPHA_TEXT

        self.extract_line += CommonString.line_feed
        
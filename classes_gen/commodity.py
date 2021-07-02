import sys
import os
import json

import classes.globals as g
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
        self.pseudo_line = False
        
        self.written_ADD = []
        self.written_ADP = []
        self.written_CVD = []
        self.written_CVP = []

    def determine_commodity_type(self):
        if self.leaf == 1:
            if self.significant_digits == 10:
                self.COMMODITY_TYPE = "2"
            else:
                self.COMMODITY_TYPE = "0"
        else:
            self.COMMODITY_TYPE = "1"
        
    def apply_commodity_inheritance(self):
        if self.leaf == 1:
            for commodity in self.hierarchy:
                for measure in commodity.measures:
                    self.measures_inherited.append(measure)
        else:
            inheritable_measure_types = ["103", "105", "305", "306"]
            if self.significant_digits > 2:
            # if self.significant_digits == 8:
                if self.productline_suffix == "80":
                    for commodity in self.hierarchy:
                        for measure in commodity.measures:
                            if measure.measure_type_id in inheritable_measure_types:
                                self.measures_inherited.append(measure)
                
                
    def sort_inherited_measures(self):
        self.measures_inherited.sort(key=lambda x: x.geographical_area_id, reverse=False)
        self.measures_inherited.sort(key=lambda x: x.priority, reverse=False)
    
    def get_supplementary_units(self, supplementary_units_reference):
        if self.leaf == 1 or (self.significant_digits >= 6 and self.productline_suffix == "80"):
            # First we need to look up the supplementary unit in the last CHIEF file, and only
            # if we can't ifnd it, do we look in CDS
            found_in_chief = False
            json_file = os.path.join(g.app.reference_folder, "supp_units.json")
            with open(json_file) as f:
                data = json.load(f)
                try:
                    item = data[self.COMMODITY_CODE]
                    self.UNIT_OF_QUANTITY = item["unit1"] + CommonString.unit_divider + item["unit2"] + CommonString.unit_divider + item["unit3"]
                    found_in_chief = True
                    pass
                except:
                    pass
                
            
            if found_in_chief == False:
                self.supplementary_unit = None
                supp_types = ['109', '110']
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
                                    found_quantity_code = True
                                    break
                        
                        if found_quantity_code == False:
                            print ("Missing supp code on comm code " + self.COMMODITY_CODE)
                        else:
                            self.UNIT_OF_QUANTITY = "1023" + CommonString.unit_divider + "2" + self.supplementary_unit.quantity_code + CommonString.unit_divider + "0000"
                            break
                        
                # If there are no units assigned then do this
                if found_quantity_code == False:
                    for unmatched in g.app.unmatched_supplementary_units:
                        if unmatched.commodity_code == self.COMMODITY_CODE:
                            self.UNIT_OF_QUANTITY = "1023" + CommonString.unit_divider + "2" + unmatched.chief_code + CommonString.unit_divider + "0000"
                            break
                else:
                    for unmatched in g.app.unmatched_supplementary_units:
                        if unmatched.commodity_code == self.COMMODITY_CODE:
                            self.UNIT_OF_QUANTITY = "1023" + CommonString.unit_divider + "2" + self.supplementary_unit.quantity_code + CommonString.unit_divider + "3" + unmatched.chief_code
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
            self.additional_code_string = "CA" + CommonString.divider
            self.additional_code_string += str(len(self.additional_codes)).rjust(4, "0") + CommonString.divider
            for additional_code in self.additional_codes:
                self.additional_code_string += additional_code + CommonString.divider

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
        else:
            self.COMMODITY_END_USE_ALLWD = "N"

    def append_footnotes_to_description(self):
        self.description_csv = f.format_string(self.description, full = False)
        if len(self.footnotes) > 0:
            for footnote in self.footnotes:
                self.description += "<" + footnote.FOOTNOTE_NUMBER + ">"
    
    def build_hierarchy_string(self):
        token = ""
        taric_token_count = 0
        self.hierarchy.append(self)
        depth = len(self.hierarchy)
        if depth > 0:
            current_depth = 0
            for item in self.hierarchy:
                current_depth += 1
                if item.significant_digits != 2: # ignore chapters
                    if item.significant_digits == 10: # We are into the Taric codes
                        taric_token_count += 1
                        if taric_token_count == 1:
                            token = "++++"
                        else:
                            if current_depth == depth:
                                token = ": - "
                            else:
                                token = ":"
                    else:
                        if current_depth == 2: # remember the chapter
                            token = ""
                        elif current_depth == 3:
                            token = ":"
                        else:
                            token = ":" + ("*" * (current_depth - 3))
                    self.hierarchy_string += token + item.description
            self.ALPHA_TEXT = self.hierarchy_string
        else:
            self.ALPHA_TEXT = self.description
        
        self.ALPHA_TEXT = f.format_string(self.ALPHA_TEXT)
        if len(self.ALPHA_TEXT) > 2200:
            self.ALPHA_TEXT = self.ALPHA_TEXT[0:2195] + "..."
        self.ALPHA_SIZE = str(len(self.ALPHA_TEXT)).zfill(4) 
            
    def get_amendment_status(self):
        # This may need to change for the second round
        if self.validity_start_date >= g.app.COMPARISON_DATE:
            self.COMMODITY_AMEND_IND = "N"
        else:
            is_amended = False
            if len(g.app.descriptions) > 0:
                for description in g.app.descriptions:
                    if description[0] == self.COMMODITY_CODE:
                        if description[1] >= g.app.COMPARISON_DATE:
                            is_amended = True
                        break
                        a = 1
                a = 1
            if is_amended:
                self.COMMODITY_AMEND_IND = "A"
            else:
                self.COMMODITY_AMEND_IND = " "
    
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
        self.extract_line += self.UNIT_OF_QUANTITY + CommonString.divider
        self.extract_line += self.ALPHA_SIZE + CommonString.divider
        self.extract_line += self.ALPHA_TEXT

        self.extract_line += CommonString.line_feed
        
    def get_entity_type(self):
        # Get the entity type - Chapter, Heading, Heading / commodity, Commodity
        if self.significant_digits == 2:
            self.entity_type = "Chapter"
        elif self.significant_digits == 4:
            if self.leaf == 1:
                self.entity_type = "Heading / commodity"
            else:
                self.entity_type = "Heading"
        else:
            self.entity_type = "Commodity"

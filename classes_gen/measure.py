import sys
from classes.functions import functions as f
import classes.globals as g
from classes.enums import CommonString


class Measure(object):
    def __init__(self):
        self.extract_line = None

        self.RECORD_TYPE = "ME" # or MX
        self.MEASURE_GROUP_CODE = "  "
        self.MEASURE_TYPE_CODE = "   "
        self.TAX_TYPE_CODE = "!!!"
        self.TARIFF_MEASURE_EDATE = "NNNNNNNN" # validity_start_date
        self.TARIFF_MEASURE_ETIME = "000000"
        self.TARIFF_MEASURE_LDATE = "00000000" # validity_end_date
        self.TARIFF_MEASURE_LTIME = "000000"
        self.ORIGIN_COUNTRY_CODE = "  "
        self.ORIGIN_COUNTRY_GROUP_CODE = "    "
        self.ORIGIN_ADD_CHARGE_TYPE = "0"
        self.DESTINATION_COUNTRY_CODE = "  "
        self.DESTINATION_CTY_GRP_CODE = "    "
        self.DESTINATION_ADD_CH_TYPE = "X"
        self.UNIT_OF_QUANTITY_CODE = "000"
        self.QUANTITY_CODE = "000" # There are odd occasions where this is 099, but I do not know why: otherwise static
        self.UNIT_ACCOUNT = "0"
        self.DUTY_TYPE = "NN"
        self.CMDTY_MEASURE_EX_HEAD_IND = "N"
        self.FREE_CIRC_DOTI_REQD_IND = "N"
        self.QUOTA_NO = "000000"
        self.QUOTA_CODE_UK = "0000" # Always four zeroes
        self.QUOTA_UNIT_OF_QUANTITY_CODE = "000"
        self.MEASURE_AMENDMENT_IND = "A"
        self.found_measure_type = False
        self.found_unit_of_quantity_code = False
        self.suppressed_geography = False
        self.members = []
        self.line_count = 0
        
        self.rates = []
        for i in range(0, 5):
            self.rates.append("0" * 23)
            
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
        index = 0
        for mc in self.measure_components:
            self.rates[index] = mc.cts_component_definition
            index += 1
            
        self.get_duty_type()
        if self.measure_type_id in ("103", "105"):
            g.app.mfns[self.goods_nomenclature_item_id] = ""
            for rate in self.rates:
                g.app.mfns[self.goods_nomenclature_item_id] += rate + CommonString.divider
        
    def get_duty_type(self):
        if len(self.measure_components) == 0:
            if self.measure_component_applicable_code == 1:
                self.DUTY_TYPE = "30" # No components, but of a type where they must be expressed in condition components
            else:
                self.DUTY_TYPE = "00" # No components

        elif len(self.measure_components) == 1:
            if self.measure_components[0].component_type == "specific":
                self.DUTY_TYPE = "01" # One component, specific
            else:
                if self.measure_components[0].duty_amount == 0:
                    self.DUTY_TYPE = "60" # One component, ad valorem and free
                else:
                    self.DUTY_TYPE = "10" # One component, ad valorem, but not free

        elif len(self.measure_components) == 2:
            if self.measure_components[0].component_type == "specific":
                self.DUTY_TYPE = "62" # The only one possible with specific first
            else:
                if self.measure_components[1].duty_expression_class == "standard":
                    self.DUTY_TYPE = "15" # Ad valorem plus specific
                elif self.measure_components[1].duty_expression_class == "minimum":
                    self.DUTY_TYPE = "95" # Ad valorem plus a minimum
                else:
                    self.DUTY_TYPE = "18" # Ad valorem plus a maximum

        elif len(self.measure_components) == 3:
            self.DUTY_TYPE = "21" # The only one possible with four components

        elif len(self.measure_components) == 4:
            self.DUTY_TYPE = "16" # The only one possible with four components

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
                    if geographical_area.suppress == "Y":
                        self.suppressed_geography = True
                    if geographical_area.has_members:
                        self.members = geographical_area.members
                    found = True
                    break
            if not found:
                self.ORIGIN_COUNTRY_GROUP_CODE = self.geographical_area_id 

    def lookup_measure_types(self, measure_types):
        if self.measure_type_id == "305":
            # All of the following are VAT
            self.found_measure_type = True
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
            self.found_measure_type = True
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
                    if measure_type.measure_type_code == "PRF": # Preferential measures need to differentiate GSP + others
                        self.found_measure_type = True
                        if self.geographical_area_id in ('2005', '2029', '2027'):
                            self.MEASURE_TYPE_CODE = "101"
                        else:
                            self.MEASURE_TYPE_CODE = "100"
                    else:
                        if measure_type.measure_type_code != "":
                            self.MEASURE_TYPE_CODE = measure_type.measure_type_code
                            self.found_measure_type = True
                        else:
                            self.found_measure_type = False

                    self.TAX_TYPE_CODE = measure_type.tax_type_code
                    break
                
        # Look up the TAPI & pharma things
        if self.additional_code_type_id == "2":
            if self.additional_code_id in ("500", "600"):
                self.MEASURE_TYPE_CODE = "X  "

        self.determine_origin_add_charge()
        self.determine_destination_country_groups()
        
    def determine_origin_add_charge(self):
        # Only used for anti-dumping duties
        # 0 – Not set
        # 1 – Definitive (measure types 552 and 554)
        # 2 – Provisional (measure types 551 and 553)
        # 3 – Mixed (never used)

        if self.MEASURE_GROUP_CODE == "AD":
            if self.measure_type_id in ("551", "553"): # Provisional
                self.ORIGIN_ADD_CHARGE_TYPE = "2"
            elif self.measure_type_id in ("552", "554"): # Definitive
                self.ORIGIN_ADD_CHARGE_TYPE = "1"
            else:
                self.ORIGIN_ADD_CHARGE_TYPE = "0"
        else:
            self.ORIGIN_ADD_CHARGE_TYPE = "0"
            
    def determine_destination_country_groups(self):
        if self.MEASURE_GROUP_CODE == "AD":
            self.DESTINATION_COUNTRY_CODE = self.ORIGIN_COUNTRY_CODE
            self.DESTINATION_CTY_GRP_CODE = self.ORIGIN_COUNTRY_GROUP_CODE
            self.DESTINATION_ADD_CH_TYPE = self.ORIGIN_ADD_CHARGE_TYPE
        else:
            self.DESTINATION_COUNTRY_CODE = "  "
            self.DESTINATION_CTY_GRP_CODE = "    "
            self.DESTINATION_ADD_CH_TYPE = "0"
            

    def create_extract_line_per_geography(self):
        self.extract_line = ""
        if self.found_measure_type == True and self.suppressed_geography == False:
            self.exclusion_list = []
            for exclusion in self.measure_excluded_geographical_areas:
                self.exclusion_list.append(exclusion.excluded_geographical_area)
            if len(self.members) == 0:
                self.create_extract_line(self.ORIGIN_COUNTRY_CODE, self.ORIGIN_COUNTRY_GROUP_CODE)
                if len(self.exclusion_list) > 0:
                    for exclusion in self.exclusion_list:
                        self.create_extract_line(exclusion, self.ORIGIN_COUNTRY_GROUP_CODE, "MX", True)
            else:
                for member in self.members:
                    if member not in self.exclusion_list:
                        self.create_extract_line(member, "    ")

    def create_extract_line(self, ORIGIN_COUNTRY_CODE, ORIGIN_COUNTRY_GROUP_CODE, RECORD_TYPE = "ME", override_rates = False):
        self.extract_line += RECORD_TYPE + CommonString.divider
        self.extract_line += self.MEASURE_GROUP_CODE + CommonString.divider
        self.extract_line += self.MEASURE_TYPE_CODE + CommonString.divider
        self.extract_line += self.TAX_TYPE_CODE + CommonString.divider
        self.extract_line += self.TARIFF_MEASURE_EDATE + CommonString.divider
        self.extract_line += self.TARIFF_MEASURE_ETIME + CommonString.divider
        self.extract_line += self.TARIFF_MEASURE_LDATE + CommonString.divider
        self.extract_line += self.TARIFF_MEASURE_LTIME + CommonString.divider
        self.extract_line += ORIGIN_COUNTRY_CODE + CommonString.divider
        self.extract_line += ORIGIN_COUNTRY_GROUP_CODE + CommonString.divider
        self.extract_line += self.ORIGIN_ADD_CHARGE_TYPE + CommonString.divider
        self.extract_line += self.DESTINATION_COUNTRY_CODE + CommonString.divider
        self.extract_line += self.DESTINATION_CTY_GRP_CODE + CommonString.divider
        self.extract_line += self.DESTINATION_ADD_CH_TYPE + CommonString.divider

        if override_rates is False:
            self.extract_line += self.rates[0] + CommonString.divider
            self.extract_line += self.rates[1] + CommonString.divider
            self.extract_line += self.rates[2] + CommonString.divider
            self.extract_line += self.rates[3] + CommonString.divider
            self.extract_line += self.rates[4] + CommonString.divider
        else:
            try:
                self.extract_line += g.app.mfns[self.goods_nomenclature_item_id]
            except:
                self.extract_line += self.rates[0] + CommonString.divider
                self.extract_line += self.rates[1] + CommonString.divider
                self.extract_line += self.rates[2] + CommonString.divider
                self.extract_line += self.rates[3] + CommonString.divider
                self.extract_line += self.rates[4] + CommonString.divider

        self.extract_line += self.DUTY_TYPE + CommonString.divider
        self.extract_line += self.CMDTY_MEASURE_EX_HEAD_IND + CommonString.divider
        self.extract_line += self.FREE_CIRC_DOTI_REQD_IND + CommonString.divider
        self.extract_line += self.QUOTA_NO + CommonString.divider
        self.extract_line += self.QUOTA_CODE_UK + CommonString.divider
        self.extract_line += self.QUOTA_UNIT_OF_QUANTITY_CODE + CommonString.divider
        self.extract_line += self.MEASURE_AMENDMENT_IND
        # self.extract_line += "   " + self.goods_nomenclature_item_id
        self.extract_line += CommonString.line_feed
        self.line_count += 1

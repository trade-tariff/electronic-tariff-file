import sys
import datetime
from classes.functions import functions as f
import classes.globals as g
from classes.enums import CommonString


class Measure(object):
    def __init__(self):
        self.extract_line = None
        self.extract_line_csv = None
        self.extract_line_mfn_csv = None

        self.RECORD_TYPE = "ME"  # or MX
        self.MEASURE_GROUP_CODE = "  "
        self.MEASURE_TYPE_CODE = "   "
        self.TAX_TYPE_CODE = "!!!"
        self.TARIFF_MEASURE_EDATE = "NNNNNNNN"  # validity_start_date
        self.TARIFF_MEASURE_ETIME = "000000"
        self.TARIFF_MEASURE_LDATE = "00000000"  # validity_end_date
        self.TARIFF_MEASURE_LTIME = "000000"
        self.ORIGIN_COUNTRY_CODE = "  "
        self.ORIGIN_COUNTRY_GROUP_CODE = "    "
        self.ORIGIN_ADD_CHARGE_TYPE = "0"
        self.DESTINATION_COUNTRY_CODE = "  "
        self.DESTINATION_CTY_GRP_CODE = "    "
        self.DESTINATION_ADD_CH_TYPE = "X"
        self.UNIT_OF_QUANTITY_CODE = "000"
        self.QUANTITY_CODE = "000"  # There are odd occasions where this is 099, but I do not know why: otherwise static
        self.UNIT_ACCOUNT = "0"
        self.DUTY_TYPE = "NN"
        self.CMDTY_MEASURE_EX_HEAD_IND = "N"
        self.FREE_CIRC_DOTI_REQD_IND = "N"
        self.QUOTA_NO = "000000"
        self.QUOTA_CODE_UK = "0000"  # Always four zeroes
        self.QUOTA_UNIT_OF_QUANTITY_CODE = "000"
        self.MEASURE_AMENDMENT_IND = "A"
        self.found_measure_type = False
        self.found_unit_of_quantity_code = False
        self.suppressed_geography = False
        self.members = []
        self.line_count = 0
        self.footnote_association_measures = []
        self.footnote_string = ""

        self.rates = []
        self.english_duty_string = ""
        for i in range(0, 5):
            self.rates.append("0" * 23)

        # Taric / CDS data
        self.measure_type_id = None
        self.measure_components = []
        self.measure_excluded_geographical_areas = []
        self.measure_conditions = []

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
            self.english_duty_string += mc.english_component_definition
            index += 1

        self.get_duty_type()
        if self.measure_type_id in ("103", "105"):
            g.app.mfns[self.goods_nomenclature_item_id] = ""
            for rate in self.rates:
                g.app.mfns[self.goods_nomenclature_item_id] += rate + CommonString.divider

    def get_duty_type(self):
        if len(self.measure_components) == 0:
            if self.measure_component_applicable_code == 1:
                self.DUTY_TYPE = "30"  # No components, but of a type where they must be expressed in condition components
            else:
                self.DUTY_TYPE = "00"  # No components

        elif len(self.measure_components) == 1:
            if self.measure_components[0].component_type == "specific":
                self.DUTY_TYPE = "01"  # One component, specific
            else:
                if self.measure_components[0].duty_amount == 0:
                    self.DUTY_TYPE = "60"  # One component, ad valorem and free
                else:
                    self.DUTY_TYPE = "10"  # One component, ad valorem, but not free

        elif len(self.measure_components) == 2:
            if self.measure_components[0].component_type == "specific":
                self.DUTY_TYPE = "62"  # The only one possible with specific first
            else:
                if self.measure_components[1].duty_expression_class == "standard":
                    self.DUTY_TYPE = "15"  # Ad valorem plus specific
                elif self.measure_components[1].duty_expression_class == "minimum":
                    self.DUTY_TYPE = "95"  # Ad valorem plus a minimum
                else:
                    self.DUTY_TYPE = "18"  # Ad valorem plus a maximum

        elif len(self.measure_components) == 3:
            self.DUTY_TYPE = "21"  # The only one possible with four components

        elif len(self.measure_components) == 4:
            self.DUTY_TYPE = "16"  # The only one possible with four components

    def resolve_geography(self, geographical_areas):
        if self.measure_sid == 20041036:
            a = 1
            pass

        if len(self.geographical_area_id) == 2:
            # Standard country or region code
            self.ORIGIN_COUNTRY_CODE = self.geographical_area_id
            self.ORIGIN_COUNTRY_GROUP_CODE = "    "
        else:
            if self.measure_type_id in ('551', '552', '553', '554') and self.geographical_area_id == "1011":
                self.ORIGIN_COUNTRY_CODE = "  "
                self.ORIGIN_COUNTRY_GROUP_CODE = "G012"
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
                    if measure_type.measure_type_code == "PRF":  # Preferential measures need to differentiate GSP + others
                        self.found_measure_type = True
                        if self.geographical_area_id in ('2005', '2020', '2027'):
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
            if self.measure_type_id in ("551", "553"):  # Provisional
                self.ORIGIN_ADD_CHARGE_TYPE = "2"
            elif self.measure_type_id in ("552", "554"):  # Definitive
                self.ORIGIN_ADD_CHARGE_TYPE = "1"
            else:
                self.ORIGIN_ADD_CHARGE_TYPE = "0"
        else:
            self.ORIGIN_ADD_CHARGE_TYPE = "0"

    def process_null(self, s):
        if s is None:
            s = ""
        return s

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
        self.extract_line_csv = ""
        self.exclusion_list = []
        self.exclusion_string = ""
        for exclusion in self.measure_excluded_geographical_areas:
            if exclusion.excluded_geographical_area not in self.exclusion_list:
                self.exclusion_list.append(exclusion.excluded_geographical_area)

        self.exclusion_list.sort()

        for exclusion in self.exclusion_list:
            self.exclusion_string += exclusion + "|"

        self.exclusion_string = self.exclusion_string.strip("|")
        self.get_exclusion_description_string()

        self.create_condition_string()
        self.create_extract_line_english()

        if self.suppressed_geography is False:
            if self.found_measure_type is True:
                if len(self.members) == 0:
                    # A country group, such as 2020 (GSP) will not have members unless it has had
                    # its CHIEF area group set to "expand"
                    self.create_extract_line(self.ORIGIN_COUNTRY_CODE, self.ORIGIN_COUNTRY_GROUP_CODE)
                    if len(self.exclusion_list) > 0:
                        for exclusion in self.exclusion_list:
                            # pass
                            self.create_extract_line(exclusion, self.ORIGIN_COUNTRY_GROUP_CODE, "MX", True)
                else:
                    for member in self.members:
                        if member not in self.exclusion_list:
                            self.create_extract_line(member, "    ")

    def get_exclusion_description_string(self):
        self.exclusions_desc = ""
        if len(self.exclusion_list) > 0:
            for e in self.exclusion_list:
                self.exclusions_desc += g.app.geographical_areas_friendly[e] + "|"

        self.exclusions_desc = self.exclusions_desc.strip("|")

    def create_extract_line(self, ORIGIN_COUNTRY_CODE, ORIGIN_COUNTRY_GROUP_CODE, RECORD_TYPE="ME", override_rates=False):
        self.RECORD_TYPE = RECORD_TYPE
        self.get_amendment_indicator()
        self.extract_line += self.RECORD_TYPE + CommonString.divider
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

        # Because we are only showing one record for each of these types, we have to mask the rates
        if self.MEASURE_TYPE_CODE in ("ADD", "ADP", "CVD", "CVP"):
            for i in range(0, 5):
                self.rates[i] = '00000000000000000000000'

        if override_rates is False:
            self.extract_line += self.rates[0] + CommonString.divider
            self.extract_line += self.rates[1] + CommonString.divider
            self.extract_line += self.rates[2] + CommonString.divider
            self.extract_line += self.rates[3] + CommonString.divider
            self.extract_line += self.rates[4] + CommonString.divider
        else:
            try:
                self.extract_line += g.app.mfns[self.goods_nomenclature_item_id]
            except Exception as e:
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
        self.extract_line += CommonString.line_feed
        if self.RECORD_TYPE != "MX":
            self.line_count += 1

    def get_amendment_indicator(self):
        if self.operation_date is None:
            self.MEASURE_AMENDMENT_IND = " "
        else:
            if self.operation_date > g.app.COMPARISON_DATE.date():
                try:
                    if self.validity_start_date > g.app.COMPARISON_DATE.date():
                        self.MEASURE_AMENDMENT_IND = "N"
                    else:
                        self.MEASURE_AMENDMENT_IND = "A"
                except Exception as e:
                    self.MEASURE_AMENDMENT_IND = " "
            else:
                self.MEASURE_AMENDMENT_IND = " "

    def create_condition_string(self):
        # condition:Y,certificate:Y945,action:29|condition:Y,certificate:Y946,action:29|condition:Y,action:09
        # condition:B,certificate:N853,action:29|condition:B,certificate:Y058,action:29|
        # condition:B,certificate:Y072,action:29|condition:B,certificate:Y073,action:29|
        # condition:B,certificate:Y076,action:29|condition:B,certificate:Y077,action:29|
        # condition:B,certificate:Y078,action:29|condition:B,certificate:Y079,action:29|
        # condition:B,certificate:C084,action:29|condition:B,action:09|condition:E,certificate:N853,action:29|condition:E,action:29|condition:E,certificate:Y072,action:29|condition:E,certificate:Y073,action:29|condition:E,certificate:Y076,action:29|condition:E,certificate:Y077,action:29|condition:E,certificate:Y078,action:29|condition:E,certificate:Y079,action:29|condition:E,certificate:C084,action:29|condition:E,action:09
        self.conditions_string = ""
        measure_condition_count = len(self.measure_conditions)
        index = 0
        for mc in self.measure_conditions:
            index += 1
            s = "condition:" + mc.condition_code
            if mc.certificate_type_code is not None:
                s += ",certificate:" + mc.certificate_type_code + mc.certificate_code
            elif mc.condition_duty_amount is not None:
                s += ",threshold:" + str(mc.condition_duty_amount) + " " + str(mc.condition_measurement_unit_code)
                if mc.condition_measurement_unit_qualifier_code is not None:
                    s += " " + mc.condition_measurement_unit_qualifier_code
                    print(self.goods_nomenclature_item_id)

            if mc.action_code is not None:
                s += ",action:" + mc.action_code
            if index < measure_condition_count:
                s += "|"
            self.conditions_string += s
        pass

    def create_extract_line_english(self):
        self.additional_code_type_id = self.process_null(self.additional_code_type_id)
        self.additional_code_id = self.process_null(self.additional_code_id)
        self.additional_code_code = self.additional_code_type_id + self.additional_code_id
        if self.additional_code_sid is not None:
            try:
                self.additional_code_description = g.app.additional_codes_friendly[self.additional_code_sid]
            except Exception as e:
                self.additional_code_description = ""
        else:
            self.additional_code_description = ""
        self.measure__reduction_indicator = ""

        self.extract_line_csv = ""
        # self.extract_line_csv += str(self.goods_nomenclature_sid) + CommonString.comma
        self.extract_line_csv += "COMMODITY_SID_PLACEHOLDER" + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + "COMMODITY_CODE_PLACEHOLDER" + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += str(self.measure_sid) + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + self.measure_type_id + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + g.app.measure_types_friendly[self.measure_type_id] + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + self.additional_code_code + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + self.additional_code_description + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + self.english_duty_string + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + self.validity_start_date + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + self.process_null(self.validity_end_date) + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += self.measure__reduction_indicator + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + self.footnote_string + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + self.conditions_string + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += str(self.geographical_area_sid) + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + self.geographical_area_id + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + g.app.geographical_areas_friendly[self.geographical_area_id] + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + self.exclusion_string + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + self.exclusions_desc + CommonString.quote_char + CommonString.comma
        self.extract_line_csv += CommonString.quote_char + self.process_null(self.ordernumber) + CommonString.quote_char
        self.extract_line_csv += CommonString.line_feed

        # self.mfn_csv_file.write(
        # '"commodity__sid",
        # "commodity__code",
        # "measure__sid",
        # "measure__type__id",
        # "measure__type__description",
        # "measure__additional_code__code",
        # "measure__additional_code__description",
        # "measure__duty_expression",
        # "measure__effective_start_date",
        # "measure__effective_end_date"' + CommonString.line_feed)

        self.extract_line_mfn_csv = ""
        # self.extract_line_mfn_csv += str(self.goods_nomenclature_sid) + CommonString.comma
        self.extract_line_mfn_csv += "COMMODITY_SID_PLACEHOLDER" + CommonString.comma
        self.extract_line_mfn_csv += CommonString.quote_char + "COMMODITY_CODE_PLACEHOLDER" + CommonString.quote_char + CommonString.comma
        self.extract_line_mfn_csv += CommonString.quote_char + "COMMODITY_CODE_DESCRIPTION" + CommonString.quote_char + CommonString.comma
        self.extract_line_mfn_csv += str(self.measure_sid) + CommonString.comma
        self.extract_line_mfn_csv += CommonString.quote_char + self.measure_type_id + CommonString.quote_char + CommonString.comma
        self.extract_line_mfn_csv += CommonString.quote_char + g.app.measure_types_friendly[self.measure_type_id] + CommonString.quote_char + CommonString.comma
        self.extract_line_mfn_csv += CommonString.quote_char + self.additional_code_code + CommonString.quote_char + CommonString.comma
        self.extract_line_mfn_csv += CommonString.quote_char + self.additional_code_description + CommonString.quote_char + CommonString.comma
        self.extract_line_mfn_csv += CommonString.quote_char + self.english_duty_string + CommonString.quote_char + CommonString.comma
        self.extract_line_mfn_csv += CommonString.quote_char + self.validity_start_date + CommonString.quote_char + CommonString.comma
        self.extract_line_mfn_csv += CommonString.quote_char + self.process_null(self.validity_end_date) + CommonString.quote_char + CommonString.comma

        self.extract_line_mfn_csv += CommonString.line_feed
        a = 1

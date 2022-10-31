from re import S
import sys
import classes_next_gen.globals as g


class Measure(object):
    def __init__(self, row):
        self.divider = "|"
        self.divider = ""
        self.row = row
        self.measure_sid = row[0]
        self.goods_nomenclature_item_id = row[1]
        self.geographical_area_id = row[2]
        self.measure_type_id = row[3]
        self.ordernumber = row[4] if row[4] is not None else "000000"
        self.additional_code = row[5] if row[5] is not None else ""
        self.goods_nomenclature_sid = row[6]
        self.validity_start_date = row[7]
        self.validity_end_date = row[8] if row[8] is not None else ""
        self.measure_priority = row[9]
        self.measure_component_applicable_code = row[10]
        self.trade_movement_code = int(row[11])
        self.measure_type_description = row[12]
        self.reduction_indicator = str(row[13]) if row[13] is not None else ""
        self.geographical_area_sid = row[14]
        self.operation_date = row[15]
        self.measure_components = []
        self.measure_conditions = []
        self.footnotes = []
        self.certificates = []
        self.measure_excluded_geographical_areas = []
        self.measure_record = ""
        self.compound_key = self.goods_nomenclature_item_id + "_" + self.measure_type_id + "_" + self.geographical_area_id
        self.is_duplicate = False
        self.duty_records = []
        self.measure_component_string = ""
        self.footnote_string = ""
        self.measure_condition_string = ""

        self.get_import_export()
        self.get_date_fields()
        self.check_for_gsp_membership()
        self.check_measure_type()
        self.check_for_erga_omnes()
        self.check_suppressed_geo_areas()
        self.get_additional_code_parts()
        # self.get_measure_group_code()
        # self.get_geographical_area_codes()
        # self.determine_origin_add_charge()
        # self.determine_destination_country_groups()
        self.create_empty_duty_records()
        self.check_for_supplementary_unit()
        self.get_additional_code_description()
        self.get_geographical_area_description()

    def get_additional_code_description(self):
        if self.additional_code == "":
            self.additional_code_description = ""
        else:
            self.additional_code_description = g.all_additional_codes_dict[self.additional_code].description

    def get_geographical_area_description(self):
        try:
            self.geographical_area_description = g.all_geographies_dict[self.geographical_area_sid].description
        except Exception as e:
            self.geographical_area_description = "Not found"

    def check_for_supplementary_unit(self):
        su_types = ['109', '110', '111']
        if self.measure_type_id in su_types:
            self.is_supplementary_unit = True
        else:
            self.is_supplementary_unit = False

    def get_import_export(self):
        if self.trade_movement_code == 0:
            self.is_import = True
            self.is_export = False
            self.trade_direction = "Import"
        elif self.trade_movement_code == 1:
            self.is_import = False
            self.is_export = True
            self.trade_direction = "Export"
        elif self.trade_movement_code == 2:
            self.is_import = True
            self.is_export = True
            self.trade_direction = "Import / Export"

    def create_empty_duty_records(self):
        pro_forma = "00000000000000000000000"
        for i in range(0, 5):
            self.duty_records.append(pro_forma)
        a = 1

    def get_geographical_area_codes(self):
        if len(self.geographical_area_id) == 2:
            # Standard 2-character country codes use the same code as CDS
            self.ORIGIN_COUNTRY_CODE = self.geographical_area_id
            self.ORIGIN_COUNTRY_GROUP_CODE = "    "
        else:
            if self.is_trade_remedy and self.is_erga_omnes:
                self.ORIGIN_COUNTRY_CODE = "  "
                self.ORIGIN_COUNTRY_GROUP_CODE = "G012"
            else:
                # Country groups need to be looked up in the list of geographical areas
                self.ORIGIN_COUNTRY_CODE = "  "
                found = False
                for geographical_area in g.geographical_areas:
                    if self.geographical_area_id == geographical_area.taric_area:
                        self.ORIGIN_COUNTRY_GROUP_CODE = geographical_area.chief_area
                        if geographical_area.has_members:
                            self.members = geographical_area.members
                            self.ORIGIN_COUNTRY_CODE = ""
                            self.ORIGIN_COUNTRY_GROUP_CODE = "EXPAND"
                        found = True
                        break
                if not found:
                    self.ORIGIN_COUNTRY_GROUP_CODE = self.geographical_area_id

        # Override for PR measures on Erga Omnes
        if self.geographical_area_id == "1011":
            if self.MEASURE_GROUP_CODE == "PR":
                self.ORIGIN_COUNTRY_GROUP_CODE = "G012"

    def get_date_fields(self):
        self.TARIFF_MEASURE_ETIME = "000000"
        self.TARIFF_MEASURE_LTIME = "000000"
        self.TARIFF_MEASURE_EDATE = self.validity_start_date.replace("-", "")
        self.validity_start_date_string = self.validity_start_date
        if self.validity_end_date != "":
            self.TARIFF_MEASURE_LDATE = self.validity_end_date.replace("-", "")
        else:
            self.TARIFF_MEASURE_LDATE = "00000000"
        a = 1

    def check_suppressed_geo_areas(self):
        suppressed_areas = ['1006']
        self.is_suppressed = True if self.geographical_area_id in suppressed_areas else False

    def check_for_gsp_membership(self):
        gsp_areas = ['2005', '2020', '2027']
        self.is_gsp = True if self.geographical_area_id in gsp_areas else False

    def check_measure_type(self):
        trade_remedy_measure_types = ['551', '552', '553', '554']
        mfn_measure_types = ['103', '105']
        supplementary_unit_measure_types = ['109', '110', '111']

        self.is_trade_remedy = True if self.measure_type_id in trade_remedy_measure_types else False
        self.is_mfn = True if self.measure_type_id in mfn_measure_types else False
        self.is_supplementary_unit = True if self.measure_type_id in supplementary_unit_measure_types else False

    def check_for_erga_omnes(self):
        self.is_erga_omnes = True if self.geographical_area_id == "1011" else False

    def get_measure_group_code(self):
        if self.measure_type_id == "305":
            self.get_vat_measure_codes()
        elif self.measure_type_id == "306":
            self.get_excise_measure_codes()
        else:
            if self.measure_type_id in g.measure_types:
                self.MEASURE_GROUP_CODE = g.measure_types[self.measure_type_id].measure_group_code
                self.MEASURE_TYPE_CODE = g.measure_types[self.measure_type_id].measure_type_code
                self.TAX_TYPE_CODE = g.measure_types[self.measure_type_id].tax_type_code
            else:
                found = False
                for measure_type in g.measure_types:
                    if g.measure_types[measure_type].certificate_code != "":
                        if self.measure_type_id == g.measure_types[measure_type].taric_measure_type:
                            if g.measure_types[measure_type].certificate_code in self.certificates:
                                self.MEASURE_GROUP_CODE = g.measure_types[measure_type].measure_group_code
                                self.MEASURE_TYPE_CODE = g.measure_types[measure_type].measure_type_code
                                self.TAX_TYPE_CODE = g.measure_types[measure_type].tax_type_code
                                found = True
                                break

                if not found:
                    if self.measure_type_id not in g.measure_types_not_found:
                        g.measure_types_not_found.append(self.measure_type_id)

                    print("Measure type not found: SID / Measure type ", str(self.measure_sid), str(self.measure_type_id))
                    self.MEASURE_GROUP_CODE = ""
                    self.MEASURE_TYPE_CODE = ""
                    self.TAX_TYPE_CODE = ""

            self.check_gsp_measure_type_code()

    def check_gsp_measure_type_code(self):
        # Check special rules on preferential duties for GSP countries
        if self.MEASURE_TYPE_CODE == "PRF":
            if self.is_gsp:
                self.MEASURE_TYPE_CODE = "101"
            else:
                self.MEASURE_TYPE_CODE = "100"

    def get_vat_measure_codes(self):
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

    def get_excise_measure_codes(self):
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

    def get_additional_code_parts(self):
        if self.additional_code == "":
            self.additional_code_type_id = ""
            self.additional_code_id = ""
        else:
            self.additional_code_type_id = self.additional_code[0]
            self.additional_code_id = self.additional_code[-3:]

    def get_ex_head(self):
        self.CMDTY_MEASURE_EX_HEAD_IND = "N"
        self.FREE_CIRC_DOTI_REQD_IND = "N"
        for mc in self.measure_conditions:
            if mc.certificate_type_code == "Y":
                self.CMDTY_MEASURE_EX_HEAD_IND = "Y"
            elif mc.certificate_type_code != "Y" and mc.certificate_type_code != "":
                self.FREE_CIRC_DOTI_REQD_IND = "Y"

    def get_duty_type(self):
        if self.measure_sid == 20000000:
            a = 1
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

    def determine_origin_add_charge(self):
        # Only used for anti-dumping duties
        # 0 – Not set
        # 1 – Definitive (measure types 552 and 554)
        # 2 – Provisional (measure types 551 and 553)
        # 3 – Mixed (never used)

        provisional_types = ["551", "553"]
        definitive_types = ["552", "554"]

        if self.MEASURE_GROUP_CODE == "AD":
            if self.measure_type_id in provisional_types:  # Provisional
                self.ORIGIN_ADD_CHARGE_TYPE = "2"
            elif self.measure_type_id in definitive_types:  # Definitive
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

    def get_measure_record(self):
        self.get_amendment_indicator()
        # suppressed records are just those applied to 1006 (Canada re-imports)
        if self.measure_sid == 20041909:
            a = 1
        # self.is_duplicate = False
        if self.MEASURE_GROUP_CODE != "" and self.is_suppressed is False and self.is_duplicate is False:
            self.measure_record = "ME" + self.divider
            self.measure_record += self.MEASURE_GROUP_CODE + self.divider
            self.measure_record += self.MEASURE_TYPE_CODE + self.divider
            self.measure_record += self.TAX_TYPE_CODE + self.divider
            self.measure_record += self.TARIFF_MEASURE_EDATE + self.divider
            self.measure_record += self.TARIFF_MEASURE_ETIME + self.divider
            self.measure_record += self.TARIFF_MEASURE_LDATE + self.divider
            self.measure_record += self.TARIFF_MEASURE_LTIME + self.divider
            self.measure_record += self.ORIGIN_COUNTRY_CODE + self.divider
            self.measure_record += self.ORIGIN_COUNTRY_GROUP_CODE + self.divider
            self.measure_record += self.ORIGIN_ADD_CHARGE_TYPE + self.divider
            self.measure_record += self.DESTINATION_COUNTRY_CODE + self.divider
            self.measure_record += self.DESTINATION_CTY_GRP_CODE + self.divider
            self.measure_record += self.DESTINATION_ADD_CH_TYPE + self.divider
            for duty_record in self.duty_records:
                self.measure_record += duty_record + self.divider
            self.measure_record += self.DUTY_TYPE + self.divider
            self.measure_record += self.CMDTY_MEASURE_EX_HEAD_IND + self.divider
            self.measure_record += self.FREE_CIRC_DOTI_REQD_IND + self.divider
            self.measure_record += self.ordernumber + self.divider
            self.measure_record += "0000" + self.divider
            self.measure_record += "000" + self.divider
            self.measure_record += self.MEASURE_AMENDMENT_IND + self.divider
            if self.ORIGIN_COUNTRY_GROUP_CODE != "    ":
                self.measure_template = "MX" + self.measure_record[2:38] + "$$" + self.measure_record[40:185]
            else:
                self.measure_template = ""
        else:
            self.measure_record = ""

        self.get_measure_record_for_csv()

    def get_amendment_indicator(self):
        if self.operation_date is None:
            self.MEASURE_AMENDMENT_IND = " "
        else:
            if self.operation_date > g.COMPARISON_DATE.date():
                try:
                    if self.validity_start_date > g.COMPARISON_DATE.date():
                        self.MEASURE_AMENDMENT_IND = "N"
                    else:
                        self.MEASURE_AMENDMENT_IND = "A"
                except Exception as e:
                    self.MEASURE_AMENDMENT_IND = " "
            else:
                self.MEASURE_AMENDMENT_IND = " "

    def get_excluded_area_string(self):
        self.excluded_area_string = ""
        self.excluded_area_description_string = ""
        if len(self.measure_excluded_geographical_areas) > 0:
            self.measure_excluded_geographical_areas.sort(key=lambda x: x.excluded_geographical_area, reverse=False)
            area_ids = []
            area_descriptions = []
            for area in self.measure_excluded_geographical_areas:
                area.description = g.all_geographies_dict[area.geographical_area_sid].description
                a = 1
                area_ids.append(area.excluded_geographical_area)
                area_descriptions.append(area.description)
            self.excluded_area_string = "|".join(area_ids)
            self.excluded_area_description_string = "|".join(area_descriptions)
            a = 1

    def get_footnote_string(self):
        self.footnote_string = ""
        if len(self.footnotes) > 0:
            self.footnotes.sort()
            self.footnote_string = "|".join(self.footnotes)

    def get_measure_condition_string(self):
        self.measure_condition_string = ""
        condition_strings = []
        if len(self.measure_conditions) > 0:
            for measure_condition in self.measure_conditions:
                condition_strings.append(measure_condition.csv_string)

            self.measure_condition_string = "|".join(condition_strings)

    def get_measure_component_string(self):
        self.measure_component_string = ""
        component_strings = []
        if len(self.measure_components) > 0:
            for measure_component in self.measure_components:
                component_strings.append(measure_component.english_component_definition)

            self.measure_component_string = " ".join(component_strings)
            self.measure_component_string = self.measure_component_string.replace("  ", " ").strip()

    def get_measure_record_for_csv(self):
        self.get_excluded_area_string()
        self.get_measure_condition_string()
        self.get_measure_component_string()
        self.get_footnote_string()
        Q = '"'
        s = ""
        s += "GOODS_NOMENCLATURE_SID" + ","
        s += Q + "GOODS_NOMENCLATURE_ITEM_ID" + Q + ","
        s += str(self.measure_sid) + ","
        s += Q + self.measure_type_id + Q + ","
        s += Q + self.measure_type_description + Q + ","
        s += Q + self.additional_code + Q + ","
        s += Q + self.additional_code_description + Q + ","
        s += Q + self.measure_component_string + Q + ","
        s += Q + self.validity_start_date + Q + ","
        s += Q + self.validity_end_date + Q + ","
        s += self.reduction_indicator + ","
        s += Q + self.footnote_string + Q + ","
        s += Q + self.measure_condition_string + Q + ","
        s += str(self.geographical_area_sid) + ","
        s += Q + self.geographical_area_id + Q + ","
        s += Q + self.geographical_area_description + Q + ","
        s += Q + self.excluded_area_string + Q + ","
        s += Q + self.excluded_area_description_string + Q + ","
        s += Q + self.ordernumber + Q + "," if self.ordernumber != "000000" else Q + Q + ","
        s += Q + self.trade_direction + Q

        self.measure_record_for_csv = s

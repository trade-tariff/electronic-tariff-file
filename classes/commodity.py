import re
from unidecode import unidecode

import classes.globals as g


class Commodity(object):
    def __init__(self, row):
        self.row = row
        self.goods_nomenclature_sid = row[0]
        self.goods_nomenclature_item_id = row[1]
        self.productline_suffix = row[2]
        self.number_indents = row[3]
        self.description = row[4] if row[4] is not None else ""
        self.validity_start_date = row[5]
        self.validity_end_date = row[6]
        self.description_start_date = row[7]
        self.description_end_date = row[8]
        self.indent_start_date = row[9]
        self.indent_end_date = row[10]
        self.ancestors = []
        self.children = []
        self.footnotes = []
        self.export_umbrella = False
        self.end_line = False
        self.writable = False
        # self.divider = "|"
        self.divider = ""
        self.chapter = self.goods_nomenclature_item_id[0:2]
        self.heading = self.goods_nomenclature_item_id[0:4]
        self.subheading6 = self.goods_nomenclature_item_id[0:6]
        self.subheading8 = self.goods_nomenclature_item_id[0:8]
        self.measures = []
        self.measure_sids = []
        self.EC_SUPP_CODE_IND = "I"
        self.COMMODITY_END_USE_ALLWD = ""
        self.supplementary_units = []
        self.ancestry_string = ""
        self.additional_codes = []
        self.additional_code_string = ""
        self.ancestry_string_length = ""
        self.commodity__code__pls = (
            self.goods_nomenclature_item_id + "-" + self.productline_suffix
        )

        self.get_significant_digits()
        self.format_dates()
        self.format_description()
        self.normalise_indent()
        self.get_spv()
        self.get_static_fields()

    def get_supplementary_units(self, include_additional=False):
        # Set the default: 1st is always kilogram, 2nd and 3rd are initially empty
        self.supplementary_units = ["1023", "0000", "0000"]

        if include_additional:
            try:
                item = g.additional_supplememtary_units[self.goods_nomenclature_item_id]
                found_chief_units = True
                self.supplementary_units[0] = item["unit1"]
                self.supplementary_units[1] = item["unit2"]
                self.supplementary_units[2] = item["unit3"]
            except Exception:
                found_chief_units = False
        if not include_additional or found_chief_units is False:
            supplementary_units_list = []
            for m in self.measures:
                if m.is_supplementary_unit:
                    supplementary_units_list.append(
                        m.measure_components[0].UNIT_OF_QUANTITY_CODE
                    )
            supplementary_units_list = list(set(supplementary_units_list))
            if len(supplementary_units_list) > 0:
                index = 0
                for supplementary_unit in supplementary_units_list:
                    index += 1
                    self.supplementary_units[index] = (
                        str(index + 1) + supplementary_unit
                    )

    def get_supp_units(self):
        if not self.export_umbrella:
            for m in self.measures:
                if m.measure_type_id in ("109", "110"):
                    s = "2" + m.measure_components[0].measurement_unit_code
                    self.supplementary_units[1] = s

    def sort_measures(self):
        self.measures.sort(key=lambda x: x.geographical_area_id, reverse=False)
        self.measures.sort(key=lambda x: x.measure_type_id, reverse=False)
        self.measures.sort(key=lambda x: x.measure_priority, reverse=False)

    def get_significant_digits(self):
        if self.goods_nomenclature_item_id[-8:] == "00000000":
            self.significant_digits = 2
        elif self.goods_nomenclature_item_id[-6:] == "000000":
            self.significant_digits = 4
        elif self.goods_nomenclature_item_id[-4:] == "0000":
            self.significant_digits = 6
        elif self.goods_nomenclature_item_id[-2:] == "00":
            self.significant_digits = 8
        else:
            self.significant_digits = 10

    def get_seasonal_rate(self):
        # The seasonal rates are not stored on the tariff database
        # Instead they are pulled from an external CSV file, so they are static
        for seasonal_rate in g.seasonal_rates:
            if seasonal_rate.goods_nomenclature_sid in self.ancestors:
                self.END_OF_SEASON_DATE = seasonal_rate.to_date
                self.START_OF_SEASON_DATE = seasonal_rate.from_date
                break

    def check_end_use(self):
        self.COMMODITY_END_USE_ALLWD = "N"
        for m in self.measures:
            if m.measure_type_id == "105":
                self.COMMODITY_END_USE_ALLWD = "Y"
                break

    def get_spv(self):
        self.SPV_CODE = "       "
        for spv in g.spvs:
            if spv.goods_nomenclature_item_id == self.goods_nomenclature_item_id:
                self.SPV_CODE = spv.spv_code
                break

    def get_commodity_type(self):
        """

        COMMODITY-IMP-EXP-USE
        •	A setting of 0 means the Commodity is valid for both Imports and Exports
        •	1 means Imports only
        •	2 means Exports only

        COMMODITY-TYPE
        0 - All trade
        1 - EC trade only (8 digit commodity codes)
        2 - Third Country trade only (10 digit commodity codes)

        """
        if self.end_line:
            # If it is an end-line, then
            # it can always be used for import and export
            self.commodity_class = "Commodity"
            self.COMMODITY_IMP_EXP_USE = "0"

            if self.significant_digits >= 9:
                self.COMMODITY_TYPE = "2"
            else:
                self.COMMODITY_TYPE = "0"
        else:
            # If it is not an end-line, then
            if self.significant_digits >= 9:
                self.COMMODITY_IMP_EXP_USE = "1"
            else:
                self.COMMODITY_IMP_EXP_USE = "2"

            self.COMMODITY_TYPE = "1"

            if self.significant_digits > 4:
                self.commodity_class = "Subheading"
            elif self.significant_digits == 4:
                self.commodity_class = "Heading"
            elif self.significant_digits == 2:
                self.commodity_class = "Chapter"

    def format_dates(self):
        self.COMMODITY_EDATE = self.validity_start_date.strftime("%Y%m%d")
        self.validity_start_date_string = self.validity_start_date.strftime("%Y-%m-%d")
        self.COMMODITY_ETIME = "000000"
        if self.validity_end_date.strftime("%Y-%m-%d") == "2999-12-31":
            self.COMMODITY_LDATE = "00000000"
            self.validity_end_date_string = ""
        else:
            self.COMMODITY_LDATE = self.validity_end_date.strftime("%Y%m%d")
            self.validity_end_date_string = self.validity_end_date.strftime("%Y-%m-%d")
        self.COMMODITY_LTIME = "000000"

    def format_description(self):
        self.description = self.description.replace('"', "'")
        self.description = re.sub(r"<br>", " ", self.description)
        self.description = re.sub(r"\r", " ", self.description)
        self.description = re.sub(r"\n", " ", self.description)
        self.description = re.sub(r"[ ]{2,10}", " ", self.description)
        self.description = unidecode(self.description)

        self.description_csv = self.description.replace('"', "'")

    def get_ancestral_descriptions(self):
        pre_taric_tokens = [
            "",
            ":",
            ":*",
            ":**",
            ":***",
            ":****",
            ":*****",
            ":******",
            ":*******",
        ]
        self.ancestral_tokens = []
        self.ancestral_significant_digits = []
        self.ancestral_descriptions = []
        for ancestor in self.ancestors:
            if g.commodities_dict[ancestor].number_indents > 0:
                self.ancestral_descriptions.append(
                    g.commodities_dict[ancestor].description
                )
                self.ancestral_significant_digits.append(
                    g.commodities_dict[ancestor].significant_digits
                )
        self.ancestral_descriptions.reverse()
        self.ancestral_significant_digits.reverse()
        self.ancestral_descriptions.append(self.description)
        self.ancestral_significant_digits.append(self.significant_digits)
        self.ancestry_string = ""
        post_taric_token_added = False

        for i in range(0, len(self.ancestral_descriptions)):
            if self.ancestral_significant_digits[i] == 10:
                if not post_taric_token_added:
                    self.ancestry_string += "++++" + self.ancestral_descriptions[i]
                    post_taric_token_added = True
                else:
                    self.ancestry_string += ":"
                    if i == len(self.ancestral_descriptions) - 1:
                        self.ancestry_string += " - "
                    self.ancestry_string += self.ancestral_descriptions[i]
            else:
                self.ancestry_string += (
                    pre_taric_tokens[i] + self.ancestral_descriptions[i]
                )

        # Shorten extremely long ancestry strings
        if len(self.ancestry_string) > 2200:
            self.ancestry_string = self.ancestry_string[0:2195] + "..."

        # Set the string length
        self.ancestry_string_length = str(len(self.ancestry_string)).zfill(4)

    def check_export_umbrella(self):
        self.export_umbrella = False
        if self.productline_suffix == "80" and self.end_line is False:
            if self.significant_digits == 8:
                self.export_umbrella = True
            else:
                for child in self.children:
                    if (
                        g.commodities_dict[child].end_line
                        and g.commodities_dict[child].significant_digits >= 9
                    ):
                        self.export_umbrella = True
                        break

    def get_static_fields(self):
        self.record_type = "CM"
        self.WAREHOUSE_COMMODITY_IND = "N"
        # self.COMMODITY_AMEND_IND = "A"
        self.COMMODITY_AMEND_IND = " "
        self.END_OF_SEASON_DATE = "000000"
        self.START_OF_SEASON_DATE = "000000"
        self.COMMODITY_TYPE = "0"
        self.COMMODITY_IMP_EXP_USE = "0"

    def normalise_indent(self):
        self.number_indents_real = self.number_indents * 1
        if self.goods_nomenclature_item_id[-8:] == "00000000":
            self.number_indents = 0
        else:
            self.number_indents += 1

    def get_measure_records(self):
        for m in self.measures:
            m.get_measure_record()

    def check_writable(self):
        if self.productline_suffix != "80" and self.number_indents <= 1:
            self.writable = False
        else:
            if self.end_line:
                self.writable = True
            else:
                if self.export_umbrella:
                    self.writable = True
                else:
                    self.writable = False

    def append_footnotes_to_description(self):
        if len(self.footnotes) > 0:
            for footnote in self.footnotes:
                self.description += "<" + footnote.FOOTNOTE_NUMBER + ">"

    def get_additional_code_string(self):
        # Take all the measures from the measures and apply to the commodity code
        # Ignore the VAT and excise-related additional codes though
        self.additional_codes_import = []
        self.additional_codes_export = []
        for m in self.measures:
            if m.additional_code_type_id not in ("X", "V", ""):
                self.additional_codes.append(m.additional_code)
                if m.is_import:
                    self.additional_codes_import.append(m.additional_code)
                if m.is_export:
                    self.additional_codes_export.append(m.additional_code)

        if len(self.additional_codes) > 0:
            self.additional_codes = sorted(self.additional_codes)
            self.additional_code_string = (
                "CA"
                + str(len(self.additional_codes)).zfill(4)
                + "".join(self.additional_codes)
            )
        else:
            self.additional_code_string = ""
        self.get_additional_code_indicator()

    def get_additional_code_indicator(self):
        """
        CODE IMPORT          EXPORT
        E    Optional        Optional
        F    Optional        Not Applicable
        G    Not Applicable  Mandatory - there can't be any of these while there are few export measures
        H    Not Applicable  Optional
        I    Not Applicable  Not Applicable
        """
        if len(self.additional_codes_import) > 0:
            if len(self.additional_codes_export) > 0:
                self.EC_SUPP_CODE_IND = "E"
            else:
                self.EC_SUPP_CODE_IND = "F"
        elif len(self.additional_codes_export) > 0:
            self.EC_SUPP_CODE_IND = "H"
        else:
            self.EC_SUPP_CODE_IND = "I"

    def get_commodity_record(self):
        self.get_commodity_record_for_csv()
        s = ""
        s += self.record_type + self.divider
        s += self.goods_nomenclature_item_id + self.divider
        s += self.COMMODITY_EDATE + self.divider
        s += self.COMMODITY_ETIME + self.divider
        s += self.COMMODITY_LDATE + self.divider
        s += self.COMMODITY_LTIME + self.divider
        s += self.EC_SUPP_CODE_IND + self.divider
        s += self.END_OF_SEASON_DATE + self.divider
        s += self.START_OF_SEASON_DATE + self.divider
        s += self.SPV_CODE + self.divider
        s += self.COMMODITY_TYPE + self.divider
        s += self.WAREHOUSE_COMMODITY_IND + self.divider
        s += self.COMMODITY_END_USE_ALLWD + self.divider
        s += self.COMMODITY_IMP_EXP_USE + self.divider
        s += self.COMMODITY_AMEND_IND + self.divider
        for su in self.supplementary_units:
            s += su + self.divider
        s += self.ancestry_string_length + self.divider
        s += self.ancestry_string + self.divider

        self.commodity_record = s

    def get_commodity_record_for_csv(self):
        ancestors_reversed = self.ancestors
        ancestors_reversed.reverse()
        ancestors_commodity__code__pls = []
        for ancestor in ancestors_reversed:
            ancestors_commodity__code__pls.append(
                g.commodities_dict[ancestor].commodity__code__pls
            )
        Q = '"'
        s = ""
        s = str(self.goods_nomenclature_sid) + ","
        s += Q + self.goods_nomenclature_item_id + Q + ","
        s += Q + self.productline_suffix + Q + ","
        s += self.validity_start_date_string + ","
        s += self.validity_end_date_string + ","
        s += Q + self.description_csv + Q + ","
        s += str(self.number_indents_real) + ","
        s += Q + self.commodity_class + Q + ","
        s += Q + "Yes" + Q + "," if self.end_line else Q + "No" + Q + ","
        s += Q + self.commodity__code__pls + Q + ","
        s += Q + ",".join(str(ancestor) for ancestor in ancestors_reversed) + Q + ","
        s += Q + ",".join(ancestors_commodity__code__pls) + Q

        self.commodity_record_for_csv = s

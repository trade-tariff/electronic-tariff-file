import sys
import math
import classes.globals as g


class MeasureComponent(object):
    def __init__(self):
        self.goods_nomenclature_item_id = None
        self.measure_sid = None
        self.duty_expression_id = None
        self.duty_amount = None
        self.monetary_unit_code = None
        self.measurement_unit_code = None
        self.measurement_unit_qualifier_code = None
        self.component_type = None

        self.UNIT_OF_QUANTITY_CODE = "000"  # Three digits
        self.QUANTITY_CODE = "000"  # Three digits (always 000)
        self.UNIT_ACCOUNT = "0"  # One digit (the currency: 0 if ad valorem, 1 if specific (or 2))
        self.SPECIFIC_RATE = "0000000000"  # Ten digits
        self.AD_VALOREM_RATE = "000000"

        self.cts_component_definition = ""
        self.english_component_definition = ""
        self.duty_expression_class = None

    def get_cts_component_definition(self):
        self.get_duty_expression_class()
        self.cts_component_definition = ""
        if self.measurement_unit_code is not None:
            # This is a SPECIFIC_RATE
            self.component_type = "specific"
            self.UNIT_ACCOUNT = "1"  # This may need to be 2 (I don't know)

            # Create a concatenated "measure" variable to represent the MUC and MUQC
            self.measure = self.measurement_unit_code.strip()
            if self.measurement_unit_qualifier_code is not None:
                self.measure += self.measurement_unit_qualifier_code.strip()

            # Get the measure unit from the supplementary units lookup
            try:
                self.UNIT_OF_QUANTITY_CODE = g.app.supplementary_unit_dict[self.measure]
            except Exception as e:
                self.UNIT_OF_QUANTITY_CODE = "000"

            self.SPECIFIC_RATE = self.pad_multiply_value(self.duty_amount, 10)
            self.AD_VALOREM_RATE = "000000"
        else:
            # This is an AD_VALOREM_RATE
            self.component_type = "advalorem"
            self.UNIT_ACCOUNT = "0"  # Means there is no currency associated with component
            self.SPECIFIC_RATE = "0000000000"
            self.AD_VALOREM_RATE = self.pad_multiply_value(self.duty_amount, 6)

        self.cts_component_definition = self.UNIT_OF_QUANTITY_CODE
        self.cts_component_definition += self.QUANTITY_CODE
        self.cts_component_definition += self.UNIT_ACCOUNT
        self.cts_component_definition += self.SPECIFIC_RATE
        self.cts_component_definition += self.AD_VALOREM_RATE

        self.get_english_component_definition()

    def get_english_component_definition(self):
        self.english_component_definition = ""
        if self.monetary_unit_code is None:
            self.monetary_unit_code = ""
        if self.measurement_unit_code is None:
            self.measurement_unit_code = ""
        if self.measurement_unit_qualifier_code is None:
            self.measurement_unit_qualifier_code = ""

        if self.duty_expression_id == "01":  # Ad valorem or specific
            if self.monetary_unit_code == "":
                self.english_component_definition += "{0:1.2f}".format(self.duty_amount) + "%"
            else:
                self.english_component_definition += "{0:1.3f}".format(self.duty_amount) + " " + self.monetary_unit_code
                if self.measurement_unit_code != "":
                    self.english_component_definition += " / " + self.get_measurement_unit(self.measurement_unit_code)
                    if self.measurement_unit_qualifier_code != "":
                        self.english_component_definition += " / " + self.get_measurement_unit_qualifier_code()

        elif self.duty_expression_id in ("04", "19", "20"):  # Plus % or amount
            if self.monetary_unit_code == "":
                self.english_component_definition += " + {0:1.2f}".format(self.duty_amount) + "%"
            else:
                self.english_component_definition += " + {0:1.3f}".format(self.duty_amount) + " " + self.monetary_unit_code
                if self.measurement_unit_code != "":
                    self.english_component_definition += " / " + self.get_measurement_unit(self.measurement_unit_code)
                    if self.measurement_unit_qualifier_code != "":
                        self.english_component_definition += " / " + self.get_measurement_unit_qualifier_code()

        elif self.duty_expression_id == "12":  # Agri component
            self.english_component_definition += " + AC"

        elif self.duty_expression_id == "15":  # Minimum
            if self.monetary_unit_code == "":
                self.english_component_definition += "MIN {0:1.2f}".format(self.duty_amount) + "%"
            else:
                self.english_component_definition += "MIN {0:1.3f}".format(self.duty_amount) + " " + self.monetary_unit_code
                if self.measurement_unit_code != "":
                    self.english_component_definition += " / " + self.get_measurement_unit(self.measurement_unit_code)
                    if self.measurement_unit_qualifier_code != "":
                        self.english_component_definition += " / " + self.get_measurement_unit_qualifier_code()

        elif self.duty_expression_id == "17":  # Maximum
            if self.monetary_unit_code == "":
                self.english_component_definition += "MAX {0:1.2f}".format(self.duty_amount) + "%"
            else:
                self.english_component_definition += "MAX {0:1.3f}".format(self.duty_amount) + " " + self.monetary_unit_code
                if self.measurement_unit_code != "":
                    self.english_component_definition += " / " + self.get_measurement_unit(self.measurement_unit_code)
                    if self.measurement_unit_qualifier_code != "":
                        self.english_component_definition += " / " + self.get_measurement_unit_qualifier_code()

        elif self.duty_expression_id == "21":  # Sugar duty
            self.english_component_definition += " + SD"

        elif self.duty_expression_id == "27":  # Flour duty
            self.english_component_definition += " + FD"

    def get_duty_expression_class(self):
        if self.duty_expression_id in ('01', '04', '19', '20'):
            self.duty_expression_class = "standard"
        elif self.duty_expression_id in ('17', '35'):
            self.duty_expression_class = "maximum"
        elif self.duty_expression_id in ('15'):
            self.duty_expression_class = "minimum"
        elif self.duty_expression_id in ('12', '14', '21', '25', '27', '29'):
            self.duty_expression_class = "meursing"
        else:
            self.duty_expression_class = "forbidden"

    def pad_multiply_value(self, s, length):
        if s is None:
            s = 0
        else:
            s = float(s)
        s = s * 1000
        s = math.ceil(s)
        s = int(s)
        s = str(s)
        s = s.rjust(length, "0")
        return s

    def get_measurement_unit(self, s):
        if s == "ASV":
            return "% vol"  # 3302101000
        if s == "NAR":
            return "item"
        elif s == "CCT":
            return "ct/l"
        elif s == "CEN":
            return "100 p/st"
        elif s == "CTM":
            return "c/k"
        elif s == "DTN":
            return "100 kg"
        elif s == "GFI":
            return "gi F/S"
        elif s == "GRM":
            return "g"
        elif s == "HLT":
            return "hl"  # 2209009100
        elif s == "HMT":
            return "100 m"  # 3706909900
        elif s == "KGM":
            return "kg"
        elif s == "KLT":
            return "1,000 l"
        elif s == "KMA":
            return "kg met.am."
        elif s == "KNI":
            return "kg N"
        elif s == "KNS":
            return "kg H2O2"
        elif s == "KPH":
            return "kg KOH"
        elif s == "KPO":
            return "kg K2O"
        elif s == "KPP":
            return "kg P2O5"
        elif s == "KSD":
            return "kg 90 % sdt"
        elif s == "KSH":
            return "kg NaOH"
        elif s == "KUR":
            return "kg U"
        elif s == "LPA":
            return "l alc. 100%"
        elif s == "LTR":
            return "l"
        elif s == "MIL":
            return "1,000 items"
        elif s == "MTK":
            return "m2"
        elif s == "MTQ":
            return "m3"
        elif s == "MTR":
            return "m"
        elif s == "MWH":
            return "1,000 kWh"
        elif s == "NCL":
            return "ce/el"
        elif s == "NPR":
            return "pa"
        elif s == "TJO":
            return "TJ"
        elif s == "TNE":
            return "tonne"  # 1005900020
            # return "1000 kg" # 1005900020
        else:
            return s

    def get_measurement_unit_qualifier_code(self):
        qualifier_description = ""
        s = self.measurement_unit_qualifier_code
        if s == "A":
            qualifier_description = "tot alc"  # Total alcohol
        elif s == "C":
            qualifier_description = "1 000"  # Total alcohol
        elif s == "E":
            qualifier_description = "net drained wt"  # net of drained weight
        elif s == "G":
            qualifier_description = "gross"  # Gross
        elif s == "M":
            qualifier_description = "net dry"  # net of dry matter
        elif s == "P":
            qualifier_description = "lactic matter"  # of lactic matter
        elif s == "R":
            qualifier_description = "std qual"  # of the standard quality
        elif s == "S":
            qualifier_description = " raw sugar"
        elif s == "T":
            qualifier_description = "dry lactic matter"  # of dry lactic matter
        elif s == "X":
            qualifier_description = " hl"  # Hectolitre
        elif s == "Z":
            qualifier_description = "% sacchar."  # per 1% by weight of sucrose
        return qualifier_description

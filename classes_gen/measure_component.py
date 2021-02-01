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
        
        self.UNIT_OF_QUANTITY_CODE = "000" # Three digits
        self.QUANTITY_CODE = "000" # Three digits (always 000)
        self.UNIT_ACCOUNT = "0" # One digit (the currency: 0 if ad valorem, 1 if specific (or 2))
        self.SPECIFIC_RATE = "0000000000" # Ten digits
        self.AD_VALOREM_RATE = "000000"
        
        self.cts_component_definition = ""
        self.duty_expression_class = None
        
    def get_cts_component_definition(self):
        self.get_duty_expression_class()
        if self.measure_sid == -267192:
            a = 1       
        self.cts_component_definition = ""
        if self.measurement_unit_code is not None:
            # This is a SPECIFIC_RATE
            self.component_type = "specific"
            self.UNIT_ACCOUNT = "1" # This may need to be 2 (I don't know)
            
            # Create a concatenated "measure" variable to represent the MUC and MUQC
            self.measure = self.measurement_unit_code.strip()
            if self.measurement_unit_qualifier_code is not None:
                self.measure += self.measurement_unit_qualifier_code.strip()
            
            # Get the measure unit from the supplementary units lookup
            self.UNIT_OF_QUANTITY_CODE = g.app.supplementary_unit_dict[self.measure]
            
            self.SPECIFIC_RATE = self.pad_multiply_value(self.duty_amount, 10)
            self.AD_VALOREM_RATE = "000000"
        else:
            # This is an AD_VALOREM_RATE
            self.component_type = "advalorem"
            self.UNIT_ACCOUNT = "0" # Means there is no currency associated with component
            self.SPECIFIC_RATE = "0000000000"
            self.AD_VALOREM_RATE = self.pad_multiply_value(self.duty_amount, 6)

        self.cts_component_definition = self.UNIT_OF_QUANTITY_CODE
        self.cts_component_definition += self.QUANTITY_CODE
        self.cts_component_definition += self.UNIT_ACCOUNT
        self.cts_component_definition += self.SPECIFIC_RATE
        self.cts_component_definition += self.AD_VALOREM_RATE

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

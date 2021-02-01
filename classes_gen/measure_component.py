import sys
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
        self.UNIT_OF_QUANTITY_CODE = None
        
    def get_measurement_unit(self):
        if self.measurement_unit_code is not None:
            self.measure = self.measurement_unit_code.strip()
            if self.measurement_unit_qualifier_code is not None:
                self.measure += self.measurement_unit_qualifier_code.strip()
            self.UNIT_OF_QUANTITY_CODE = g.app.supplementary_unit_dict[self.measure]
            # print("self.UNIT_OF_QUANTITY_CODE", self.UNIT_OF_QUANTITY_CODE)
            pass
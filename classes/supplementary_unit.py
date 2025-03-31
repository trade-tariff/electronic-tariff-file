class SupplementaryUnit(object):
    def __init__(
        self,
        measurement_unit_code=None,
        measurement_unit_qualifier_code=None,
        quantity_code=None,
    ):
        self.measurement_unit_code = measurement_unit_code
        self.measurement_unit_qualifier_code = measurement_unit_qualifier_code
        self.quantity_code = quantity_code


class UnmatchedSupplementaryUnit(object):
    def __init__(
        self,
        commodity_code,
        measurement_unit_code,
        measurement_unit_qualifier_code,
        chief_code,
    ):
        self.commodity_code = commodity_code
        self.measurement_unit_code = measurement_unit_code
        self.measurement_unit_qualifier_code = measurement_unit_qualifier_code
        self.chief_code = chief_code

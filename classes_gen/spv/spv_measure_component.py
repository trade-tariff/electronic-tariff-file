class SPVMeasureComponent(object):
    def __init__(self, row):
        self.measure_sid = row[0]
        self.duty_expression_id = row[1]
        self.duty_amount = row[2]
        self.monetary_unit_code = row[3]
        self.measurement_unit_code = row[4]
        self.measurement_unit_qualifier_code = row[5]

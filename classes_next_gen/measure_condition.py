class MeasureCondition(object):
    def __init__(self, row):
        self.row = row
        self.measure_sid = row[0]
        self.measure_condition_sid = row[1]
        self.condition_code = row[2]
        self.component_sequence_number = row[3]
        self.condition_duty_amount = row[4]
        self.condition_monetary_unit_code = row[5] if row[5] is not None else ""
        self.condition_measurement_unit_code = row[6] if row[6] is not None else ""
        self.condition_measurement_unit_qualifier_code = row[7] if row[7] is not None else ""
        self.action_code = row[8]
        self.certificate_type_code = row[9] if row[9] is not None else ""
        self.certificate_code = row[10] if row[10] is not None else ""
        self.csv_string = ""

        self.conjoin_certificate()
        self.get_csv_string()

    def conjoin_certificate(self):
        self.certificate = self.certificate_type_code + self.certificate_code

    def get_csv_string(self):
        if self.certificate != "":
            self.csv_string = "condition:{condition_code},certificate:{certificate},action:{action_code}".format(
                condition_code=self.condition_code,
                certificate=self.certificate,
                action_code=self.action_code
            )
        elif self.condition_duty_amount is not None:
            threshold = "{:.2f}".format(self.condition_duty_amount)
            if self.condition_measurement_unit_code != "":
                threshold += " " + self.condition_measurement_unit_code
            if self.condition_measurement_unit_qualifier_code != "":
                threshold += " " + self.condition_measurement_unit_qualifier_code
            self.csv_string = "condition:{condition_code},threshold:{threshold},action:{action_code}".format(
                condition_code=self.condition_code,
                threshold=threshold,
                action_code=self.action_code
            )
        else:
            self.csv_string = "condition:{condition_code},action:{action_code}".format(
                condition_code=self.condition_code,
                action_code=self.action_code
            )

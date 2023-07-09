from datetime import datetime


class DeltaMeasure(object):
    def __init__(self, row, operation):
        self.operation = operation
        self.goods_nomenclature_item_id = row[0]
        self.geographical_area_id = row[1]
        self.measure_type_description = row[2]
        self.validity_start_date = row[3]
        self.validity_end_date = row[4]

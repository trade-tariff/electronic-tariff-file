from datetime import datetime


class DeltaCommodity(object):
    def __init__(self, row, operation):
        self.operation = operation
        self.goods_nomenclature_item_id = row[0]
        self.productline_suffix = row[1]
        self.description = row[2]
        validity_start_date = row[3]
        self.validity_start_date = datetime.strftime(validity_start_date, "%Y-%m-%d")
        validity_end_date = row[4]
        if validity_end_date is None:
            self.validity_end_date = ""
        else:
            self.validity_end_date = datetime.strftime(validity_end_date, "%Y-%m-%d")

class DeltaMeasure(object):
    def __init__(self, row, operation, use_materialized_views):
        self.use_materialized_views = use_materialized_views
        self.operation = operation
        self.goods_nomenclature_item_id = row[0]
        self.geographical_area_id = row[1]
        self.measure_type_description = row[2]
        self.validity_start_date = row[3]
        self.validity_end_date = row[4]

        format = "%Y-%m-%d"
        if isinstance(self.validity_start_date, str):
            self.validity_start_date_string = self.validity_start_date
        else:
            self.validity_start_date_string = self.validity_start_date.strftime(format)
        if self.validity_end_date is not None:
            if isinstance(self.validity_end_date, str):
                self.validity_end_date_string = self.validity_end_date
            else:
                self.validity_end_date_string = self.validity_end_date.strftime(format)
        else:
            self.validity_end_date_string = ""

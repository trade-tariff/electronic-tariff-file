from datetime import datetime


class SeasonalRate(object):
    def __init__(self, goods_nomenclature_item_id, from_date, to_date, seasonal_rate, prose=None):
        self.goods_nomenclature_item_id = goods_nomenclature_item_id.ljust(10, "0")
        self.from_date = self.to_date_string(from_date)
        self.to_date = self.to_date_string(to_date)
        self.seasonal_rate = seasonal_rate
        self.prose = prose

    @staticmethod
    def to_date_string(s):
        s2 = datetime.now().strftime('%y') + s[-2:] + s[:2]
        return s2
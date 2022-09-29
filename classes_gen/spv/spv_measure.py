class SPVMeasure(object):
    def __init__(self, row):
        self.measure_sid = row[0]
        self.goods_nomenclature_item_id = row[1]
        self.goods_nomenclature_sid = row[2]

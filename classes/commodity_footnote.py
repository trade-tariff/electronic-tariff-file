class CommodityFootnote(object):
    def __init__(self):
        self.goods_nomenclature_item_id = None
        self.goods_nomenclature_sid = None
        self.footnote_type_id = None
        self.footnote_id = None
        self.FOOTNOTE_NUMBER = None

    def get_footnote_number(self):
        if self.footnote_type_id == "NC":  # add 800
            self.FOOTNOTE_NUMBER = str(int(self.footnote_id) + 800)
        elif self.footnote_type_id == "PN":  # add 900
            self.FOOTNOTE_NUMBER = str(int(self.footnote_id) + 900)
        else:
            self.FOOTNOTE_NUMBER = self.footnote_id

class PrMeasure(object):
    def __init__(self, commodity, line):
        self.commodity = commodity
        self.line = line
        if len(self.line) != 185:
            self.line += " "

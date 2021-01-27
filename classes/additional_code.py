class AdditionalCode(object):
    def __init__(self, line):
        self.line = line.strip()
        self.parse()

    def parse(self):
        self.RECORD_TYPE = self.line[0:2]
        self.EC_SUPP_COUNT = self.line[2:6]

        line_length = len(self.line)
        ac_length = line_length - 6
        ac_count = int(ac_length / 4)

        self.CODE_STRING = ""
        for i in range(0, ac_count):
            self.CODE_STRING += self.line[6+(i * 4): 6 + (i * 4) + 4] + ":"
        self.CODE_STRING = self.CODE_STRING.strip(":")

        self.line = ""

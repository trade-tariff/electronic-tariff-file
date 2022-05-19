from classes.application import Application

app = Application()

class functions(object):
    @staticmethod
    def format_string(s):
        s = s.replace("é", "<KB>")
        return s

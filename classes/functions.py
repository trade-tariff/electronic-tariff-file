class functions(object):
    @staticmethod
    def format_string(s):
        s = s.replace("é", "<KB>")
        return s
    
    @staticmethod
    def YYYYMMDD(d):
        if d is None:
            return "00000000"
        elif isinstance(d, str):
            ret = d.replace("-", "")
            return ret
        else:
            ret = d.strftime("%Y%m%d")
            return ret

    @staticmethod
    def HHMMSS(d):
        if d is None:
            return "00000000"
        else:
            ret = d.strftime("%H%M%S")
            return ret

    
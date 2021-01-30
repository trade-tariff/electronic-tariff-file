class functions(object):
    @staticmethod
    def format_string(s):
        s = s.replace("ü", "<KA>")
        s = s.replace("É", "<KB>")
        s = s.replace("ê", "<KC>")
        s = s.replace("é", "<KD>")
        s = s.replace("ç", "<KE>")
        s = s.replace("è", "<KF>")
        s = s.replace("â", "<KG>")
        s = s.replace("ä", "<KH>")
        s = s.replace("ï", "<KI>")
        s = s.replace("·", "<KJ>")
        s = s.replace("È", "<KK>")
        s = s.replace("ÿ", "<KL>")
        s = s.replace("ã", "<KM>")
        s = s.replace("ñ", "<KN>")
        s = s.replace("º", "<KO>")
        s = s.replace("õ", "<KP>")
        s = s.replace("µ", "<KU>")
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

    
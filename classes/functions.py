import re


class functions(object):
    @staticmethod
    def format_string(s):
        if 'Original engravings, prints and lithographs++++Othe' in s:
            a = 1

        s = s.strip()
        s = s.replace("<br />", "<br>")
        if s[-4:] == "<br>":
            s = s[:-4]

        # Replace special characters
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
        s = s.replace("°", "<KP>")
        s = s.replace("µ", "<KU>")
        
        # Replace new lines
        s = s.replace("<br> ", "<br>")
        for i in range(0, 3):
            s = s.replace("<br><br>", "<br>")
        s = s.replace("<br>", "<AC>")
        
        # Replace superscripts & subscripts
        s = re.sub(r"\<sup\>([^\<]+)\<\/sup\>",  "<AG>!\\1!", s)
        s = re.sub(r"\<sub\>([^\<]+)\<\/sub\>",  "<AH>!\\1!", s)
        #<AG>!3! / <AH>!3!
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

    
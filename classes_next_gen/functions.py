import os
import re


class functions(object):
    @staticmethod
    def get_config_key(key, data_type, default):
        try:
            s = os.getenv(key)
            if data_type in ("int", "integer"):
                s = int(s)
        except Exception as e:
            s = default
        return s

    @staticmethod
    def YN(s):
        if str(s) == "1":
            return "Yes"
        else:
            return "No"

    @staticmethod
    def format_string(s, full=True):
        s = s.strip()
        s = s.replace("<br />", "<br>")
        if s[-4:] == "<br>":
            s = s[:-4]

        # Replace new lines
        s = s.replace("<br> ", "<br>")
        for i in range(0, 3):
            s = s.replace("<br><br>", "<br>")

        s = s.replace("|", " ")
        s = s.replace("α", "alpha")
        s = s.replace("μm", "micrometres")
        s = s.replace("μΩ", "micro-ohm")
        s = s.replace("Ω", "Ohm")
        s = s.replace("μ", "u")
        s = s.replace("β", "beta")
        s = s.replace("ß", "beta")
        s = s.replace("ω", "w")
        s = s.replace("′", "'")
        s = s.replace("γ", "y")
        s = s.replace("•", "-")
        s = s.replace("—", "-")
        s = s.replace("–", "-")
        s = s.replace("‘", "'")
        s = s.replace("’", "'")
        s = s.replace("´", "'")
        s = s.replace("λ", " lambda")
        s = s.replace("≥", ">=")
        s = s.replace("×", "x")
        s = s.replace("ø", "o")
        s = s.replace("Ο", "O")
        s = s.replace("€", "EUR")
        s = s.replace("œ", "oe")
        s = s.replace('″', '"')
        s = s.replace('“', '"')
        s = s.replace('”', '"')
        s = s.replace("−", "-")
        s = s.replace("Δ", "")
        s = s.replace("ο", "o")
        s = s.replace("≈", "")
        s = s.replace("than1", "than 1")
        # s = s.replace("", "")
        # s = s.replace("", "")
        # s = s.replace("", "")

        s = re.sub(r'\s+', ' ', s)  # Standardises the whitespace chars
        s = re.sub(r'[^\x00-\x7F]+', ' ', s)  # generically removes everything over 255 in ASCII char set

        if not full:
            s = s.replace("<br>", " ")
            s = s.replace('"', '""')
        else:
            s = s.replace("<br>", "<AC>")

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
            s = s.replace("ô", "<KP>")
            s = s.replace("°", "<KP>")
            s = s.replace("µ", "<KU>")

            # Replace superscripts & subscripts
            s = re.sub(r"\<sup\>([^\<]+)\<\/sup\>", "<AG>!\\1!", s)
            s = re.sub(r"\<sub\>([^\<]+)\<\/sub\>", "<AH>!\\1!", s)

            # New, post conversations with Descartes
            s = s.replace("±", "+/-")

            # Superscripts
            s = s.replace("⁰", "<AG>!0!")  # Becomes and Angstrom character
            s = s.replace("¹", "<AG>!1!")  # Becomes and Angstrom character
            s = s.replace("²", "<AG>!2!")  # Becomes and Angstrom character
            s = s.replace("³", "<AG>!3!")  # Becomes and Angstrom character
            s = s.replace("⁴", "<AG>!4!")  # Becomes and Angstrom character
            s = s.replace("⁵", "<AG>!5!")  # Becomes and Angstrom character
            s = s.replace("⁶", "<AG>!6!")  # Becomes and Angstrom character
            s = s.replace("⁷", "<AG>!7!")  # Becomes and Angstrom character
            s = s.replace("⁸", "<AG>!8!")  # Becomes and Angstrom character
            s = s.replace("⁹", "<AG>!9!")  # Becomes and Angstrom character

            # Subscripts
            s = s.replace("₀", "<AH>!0!")
            s = s.replace("₁", "<AH>!1!")
            s = s.replace("₂", "<AH>!2!")
            s = s.replace("₃", "<AH>!3!")
            s = s.replace("₄", "<AH>!4!")
            s = s.replace("₅", "<AH>!5!")
            s = s.replace("₆", "<AH>!6!")
            s = s.replace("₇", "<AH>!7!")
            s = s.replace("₈", "<AH>!8!")
            s = s.replace("₉", "<AH>!9!")

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

    @staticmethod
    def YYYY_MM_DD(d):
        if d is None:
            return ""
        elif isinstance(d, str):
            parts = d.split(" ")
            ret = parts[0]
            return ret
        else:
            ret = d.strftime("%Y%m%d")
            return ret

    @staticmethod
    def format_date(d, fmt):
        if d is None:
            return ""
        elif isinstance(d, str):
            parts = d.split(" ")
            ret = parts[0]
            return ret
        else:
            ret = d.strftime(fmt)
            return ret

    @staticmethod
    def null_to_string(d):
        if d is None:
            return ""
        else:
            d = str(d)
            return d.strip()

    @staticmethod
    def strip_quotes(s):
        s = s.replace('"', "'")
        return s

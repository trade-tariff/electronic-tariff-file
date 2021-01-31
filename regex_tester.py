import re
from classes.functions import functions as f

s = """Natural borates and concentrates H<sub>3</sub>BO<sub>3</sub> thereof (whether or not calcined), but not including H<sub>3</sub>BO<sub>3</sub> borates separated from natural brine; natural boric acid containing not more than 85 % of H<sub>3</sub>BO<sub>3</sub> calculated on the dry weight"""

s2 = f.format_string(s)

print(s + "\n")
print(s2)
import os
import sys
import classes.globals as g
from classes.application import Application

app = Application()

print("Finding requested folder / files ...")
os.system('open "%s"' % app.icl_vme_folder)

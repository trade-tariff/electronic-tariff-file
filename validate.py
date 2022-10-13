import sys


file = "/Users/MLavis.Admin/sites and projects/1. Online Tariff/04. electronic-tariff-file/_export2/2022-10-06/uk/icl_vme/hmrc-tariff-ascii-2022-10-06.txt"
file1 = open(file, 'r')
lines = file1.readlines()
count = 0
# Strips the newline character
for line in lines:
    count += 1
    # print("Line{}: {}".format(count, line.strip()))
    if len(line) < 10:
        sys.exit()

print(count)

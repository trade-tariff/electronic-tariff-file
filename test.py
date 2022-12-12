import os


my_path = "/Users/MLavis.Admin/sites and projects/1. Online Tariff/04. electronic-tariff-file/_export/2022-10-31/uk/icl_vme/hmrc-tariff-ascii-2022-10-31.txt"
file1 = open(my_path, 'r')
count = 0
CM_RECORD_COUNT = 0
CA_RECORD_COUNT = 0
ME_RECORD_COUNT = 0
MD_RECORD_COUNT = 0
MX_RECORD_COUNT = 0
TOTAL_RECORD_COUNT = 0

while True:
    count += 1

    # Get next line from file
    line = file1.readline()

    # if line is empty
    # end of file is reached
    if not line:
        break
    line_length = len(line)
    if len(line) < 2:
        print("Short line on {line}".format(line=str(count)))
        break

    if line[0:2] == "CM":
        CM_RECORD_COUNT += 1
    elif line[0:2] == "CA":
        CA_RECORD_COUNT += 1
    elif line[0:2] == "ME":
        ME_RECORD_COUNT += 1
    elif line[0:2] == "MX":
        MX_RECORD_COUNT += 1
    elif line[0:2] == "MD":
        MD_RECORD_COUNT += 1

TOTAL_RECORD_COUNT = CM_RECORD_COUNT + CA_RECORD_COUNT + ME_RECORD_COUNT + MX_RECORD_COUNT + MD_RECORD_COUNT

file1.close()
print(str(count))
print("Commodity records = {x}".format(x=str(CM_RECORD_COUNT)))
print("Add code records = {x}".format(x=str(CA_RECORD_COUNT)))
print("Measure records = {x}".format(x=str(ME_RECORD_COUNT)))
print("Exception records = {x}".format(x=str(MX_RECORD_COUNT)))

print("Total records = {x}".format(x=str(TOTAL_RECORD_COUNT)))

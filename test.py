import os


my_path = "/Users/MLavis.Admin/sites and projects/1. Online Tariff/04. electronic-tariff-file/_export2/2022-10-27/uk/icl_vme/hmrc-tariff-ascii-2022-10-27.txt"
file1 = open(my_path, 'r')
count = 0

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
    # print("Line{}: {}".format(count, line.strip()))

file1.close()
print(str(count))

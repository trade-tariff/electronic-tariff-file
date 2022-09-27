import csv


print("Doing")
in_file = "/Users/MLavis.Admin/sites and projects/1. Online Tariff/04. electronic-tariff-file/_export/2022-09-15/uk/csv/hmrc-tariff-measures-2022-09-15.csv"
out_file = "/Users/MLavis.Admin/sites and projects/1. Online Tariff/04. electronic-tariff-file/_export/2022-09-15/uk/csv/hmrc-tariff-measures-2022-09-15-103.csv"

reader = csv.reader(open(in_file), delimiter=',')
filtered = filter(lambda p: '103' == p[3], reader)
csv.writer(open(out_file, 'w'), delimiter=',').writerows(filtered)
print("Done")

import csv

in_file = "/Users/MLavis.Admin/sites and projects/1. Online Tariff/04. electronic-tariff-file/_export/2022-09-01/uk/csv/hmrc-tariff-measures-2022-09-01.csv"
out_file = "/Users/MLavis.Admin/sites and projects/1. Online Tariff/04. electronic-tariff-file/_export/2022-09-01/uk/csv/hmrc-tariff-measures-2022-09-01-filtered.csv"

reader = csv.reader(open(in_file), delimiter=',')
filtered = filter(lambda p: '305' == p[3], reader)
csv.writer(open(out_file, 'w'), delimiter=',').writerows(filtered)

import csv

in_file = "/Users/mattlavis/sites and projects/1. Online Tariff/electronic-tariff-file/_export/2022-06-09/uk/csv/hmrc-tariff-measures-2022-06-09.csv"
out_file = "/Users/mattlavis/sites and projects/1. Online Tariff/electronic-tariff-file/_export/2022-06-09/uk/csv/cat-2022-06-09.csv"

reader = csv.reader(open(in_file), delimiter=',')
filtered = filter(lambda p: '740' == p[3], reader)
csv.writer(open(out_file, 'w'), delimiter=',').writerows(filtered)

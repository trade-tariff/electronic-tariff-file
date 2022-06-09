import csv

in_file = "/Users/mattlavis/sites and projects/1. Online Tariff/electronic-tariff-file/_export/2022-05-19/uk/csv/hmrc-tariff-measures-2022-05-19.csv"
out_file = "/Users/mattlavis/sites and projects/1. Online Tariff/electronic-tariff-file/_export/2022-05-19/uk/csv/vat-2022-05-19.csv"

reader = csv.reader(open(in_file), delimiter=',')
filtered = filter(lambda p: '305' == p[3], reader)
csv.writer(open(out_file, 'w'), delimiter=',').writerows(filtered)

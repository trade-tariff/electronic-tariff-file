import os
import py7zr

from classes.aws_bucket import AwsBucket


def zip_extract_commodity_csv():
    zipfile = "/Users/matt.admin/sites and projects/1. Online Tariff/electronic tariff file/_export/2021-03-03/uk/csv/hmrc-tariff-commodities-03-mar-2021.7z"
    contained = "/Users/matt.admin/sites and projects/1. Online Tariff/electronic tariff file/_export/2021-03-03/uk/csv/hmrc-tariff-commodities-03-mar-2021.csv"
    filename = "hmrc-tariff-commodities-03-mar-2021.csv"
    try:
        os.remove(zipfile)
    except:
        pass
    with py7zr.SevenZipFile(zipfile, 'w') as archive:
        archive.write(contained, filename)
        
def test_aws():
    bucket = AwsBucket()
    bucket.upload_file("requirements.txt", "requirements.txt")
    pass
        
test_aws()
# zip_extract_commodity_csv()

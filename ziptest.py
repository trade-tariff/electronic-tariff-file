import os
import py7zr
import zipfile

from classes.aws_bucket import AwsBucket


def zip_extract_commodity_csv():
    zipfile = "/Users/matt.admin/sites and projects/1. Online Tariff/electronic tariff file/_export/2021-03-03/uk/csv/hmrc-tariff-commodities-03-mar-2021.7z"
    contained = "/Users/matt.admin/sites and projects/1. Online Tariff/electronic tariff file/_export/2021-03-03/uk/csv/hmrc-tariff-commodities-03-mar-2021.csv"
    filename = "hmrc-tariff-commodities-03-mar-2021.csv"
    try:
        os.remove(zipfile)
    except Exception as e:
        pass
    with py7zr.SevenZipFile(zipfile, 'w') as archive:
        archive.write(contained, filename)
        
def test_aws():
    bucket = AwsBucket()
    bucket.upload_file("requirements.txt", "requirements.txt")
    pass
    

def create_zip_archive():
    # Create the archive in ZIP format
    archive = "test.zip"
    arc = "changed.txt"
    # self.base_filename = os.path.basename(self.source_filename)
    # self.archive_base_filename = os.path.basename(self.archive)
    
    zipObj = zipfile.ZipFile(archive, 'w')
    compression = zipfile.ZIP_DEFLATED
    zipObj.write(archive, arcname=arc) #, compress_type=compression)
    # zipObj.write(self.base_filename, compress_type=compression)
    zipObj.close()

    
# test_aws()
# zip_extract_commodity_csv()
create_zip_archive()

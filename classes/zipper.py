import os
import py7zr
import zipfile
import zlib
import pyminizip
from dotenv import load_dotenv
from classes.aws_bucket import AwsBucket

import classes.globals as g


class Zipper(object):
    def __init__(self, source_filename, scope, remote_folder, message):
        # Always compresses to the same place with the default
        # file extension for the compression type
        load_dotenv('.env')
        self.create_7z = int(os.getenv('CREATE_7Z'))
        self.create_zip = int(os.getenv('CREATE_ZIP'))
        self.use_password = int(os.getenv('USE_PASSWORD'))
        self.password = os.getenv('PASSWORD')
        if g.app.start != 0 or g.app.end != 10:
            self.write_to_aws = False
        else:
            self.write_to_aws = int(os.getenv('WRITE_TO_AWS'))
        self.compress_level = 9
        
        self.scope = scope
        self.source_filename = source_filename
        self.remote_folder = remote_folder
        self.message = message

    def compress(self):
        if self.create_7z:
            ret_7z = self.create_7z_archive()
            
        if self.create_zip:
            ret_zip = self.create_zip_archive()
            
        return ret_7z, ret_zip

    def create_7z_archive(self):
        # Create the archive in 7z format
        self.archive = self.source_filename.replace(".txt", ".7z")
        self.archive = self.archive.replace(".csv", ".7z")
        self.base_filename = os.path.basename(self.source_filename)
        self.archive_base_filename = os.path.basename(self.archive)
        try:
            os.remove(self.archive)
        except:
            pass
        if self.use_password == 1:
            with py7zr.SevenZipFile(self.archive, 'w', password=self.password) as archive:
                archive.write(self.source_filename, self.base_filename)

        else:
            with py7zr.SevenZipFile(self.archive, 'w') as archive:
                archive.write(self.source_filename, self.base_filename)
                
        self.aws_path = os.path.join(self.scope, self.remote_folder, self.archive_base_filename)
        self.load_to_aws("Loading {0} (7z) to AWS bucket".format(self.message), self.archive, self.aws_path)
        return self.aws_path

    def create_zip_archive(self):
        # Create the archive in ZIP format
        self.archive = self.source_filename.replace(".txt", ".zip")
        self.archive = self.archive.replace(".csv", ".zip")
        self.base_filename = os.path.basename(self.source_filename)
        self.archive_base_filename = os.path.basename(self.archive)
        
        try:
            os.remove(self.archive)
        except:
            pass
        
        if self.use_password == 1:
            pyminizip.compress(self.source_filename, None, self.archive, self.password, self.compress_level)

        else:
            zipObj = zipfile.ZipFile(self.archive, 'w')
            compression = zipfile.ZIP_DEFLATED
            zipObj.write(self.source_filename, arcname=self.base_filename, compress_type=compression)
            zipObj.close()

        self.aws_path = os.path.join(self.scope, self.remote_folder, self.archive_base_filename)
        self.load_to_aws("Loading {0} (ZIP) to AWS bucket".format(self.message), self.archive, self.aws_path)
        return self.aws_path

    def load_to_aws(self, msg, file, aws_path):
        if self.write_to_aws == 1:
            print(msg)
            bucket = AwsBucket()
            bucket.upload_file(file, aws_path)

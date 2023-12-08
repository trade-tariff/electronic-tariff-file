import boto3
import os
from dotenv import load_dotenv


class AwsBucket(object):
    def __init__(self):
        load_dotenv(".env")

        self.BUCKET_NAME = os.getenv("BUCKET_NAME")
        self.s3_client = boto3.client("s3")

    def upload_file(self, source, destination):
        self.s3_client.upload_file(source, self.BUCKET_NAME, destination)

import boto3
import os
from dotenv import load_dotenv

from classes.enums import CommonString
from classes.sendgrid_mailer import SendgridMailer


class AwsBucket(object):
    def __init__(self):
        load_dotenv('.env')

        self.AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
        self.AWS_REGION = os.getenv('AWS_REGION')
        self.AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.BUCKET_NAME = os.getenv('BUCKET_NAME')
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY
        )

    def upload_file(self, source, destination):
        response = self.s3_client.upload_file(source, self.BUCKET_NAME, destination)
        self.url = "https://" + self.BUCKET_NAME + ".s3.amazonaws.com/" + destination

    def delete_by_pattern(self, pattern):
        # 28-mar-2021
        s3_resource = boto3.resource(
            's3',
            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY
        )
        my_bucket = s3_resource.Bucket(self.BUCKET_NAME)
        summaries = my_bucket.objects.all()
        files = []
        for file in summaries:
            if pattern in file.key:
                self.s3_client.delete_object(
                    Bucket=self.BUCKET_NAME,
                    Key=file.key
                )

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

    def upload_file(self, source, destination):
        s3_client = boto3.client(
            's3',
            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY
        )
        response = s3_client.upload_file(source, self.BUCKET_NAME, destination)
        self.url = "https://" + self.BUCKET_NAME + ".s3.amazonaws.com/" + destination



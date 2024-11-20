import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

class S3Sync:
    def __init__(self,AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY,AWS_REGION):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )

    def sync_folder_to_s3(self, folder, aws_bucket_name):
        """
        Sync a local folder to an S3 bucket.
        
        :param folder: Local folder path to sync
        :param aws_bucket_name: Name of the S3 bucket
        """
        try:
            for root, _, files in os.walk(folder):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    # Create the relative path for S3
                    relative_path = os.path.relpath(local_file_path, folder)
                    s3_file_path = os.path.join(aws_bucket_name, relative_path)

                    # Upload the file
                    self.s3_client.upload_file(local_file_path, aws_bucket_name, relative_path)
                    print(f"Uploaded {local_file_path} to s3://{aws_bucket_name}/{relative_path}")

        except (NoCredentialsError, PartialCredentialsError) as e:
            print("Credentials not available or incomplete.")
            print(e)

    def sync_folder_from_s3(self, folder, aws_bucket_name):
        """
        Sync an S3 bucket to a local folder.
        
        :param folder: Local folder path to sync
        :param aws_bucket_name: Name of the S3 bucket
        """
        try:
            # List objects in the specified S3 bucket
            response = self.s3_client.list_objects_v2(Bucket=aws_bucket_name)

            if 'Contents' in response:
                for obj in response['Contents']:
                    s3_file_path = obj['Key']
                    local_file_path = os.path.join(folder, s3_file_path)

                    # Create directories if they don't exist
                    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

                    # Download the file
                    self.s3_client.download_file(aws_bucket_name, s3_file_path, local_file_path)
                    print(f"Downloaded s3://{aws_bucket_name}/{s3_file_path} to {local_file_path}")

            else:
                print("No files found in the specified S3 bucket.")

        except (NoCredentialsError, PartialCredentialsError) as e:
            print("Credentials not available or incomplete.")
            print(e)
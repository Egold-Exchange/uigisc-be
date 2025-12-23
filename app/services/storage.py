import boto3
from botocore.exceptions import ClientError
from app.config import settings
import uuid
import os
import io

class StorageService:
    def __init__(self):
        # Extract region from endpoint if possible (e.g., https://nyc3.digitaloceanspaces.com)
        endpoint = settings.do_endpoint
        region = 'nyc3'  # default
        
        if 'digitaloceanspaces.com' in endpoint:
            try:
                # Handle cases like https://bucket.region.digitaloceanspaces.com
                parts = endpoint.split('://')[1].split('.')
                # If it's bucket.region.digitaloceanspaces.com -> parts = ['bucket', 'region', 'digitaloceanspaces', 'com']
                # If it's region.digitaloceanspaces.com -> parts = ['region', 'digitaloceanspaces', 'com']
                if len(parts) >= 4:
                    region = parts[1]
                else:
                    region = parts[0]
            except Exception:
                pass

        print(f"Initializing StorageService with region: {region}, endpoint: {endpoint}, bucket: {settings.do_bucket}")
        self.session = boto3.session.Session()
        self.client = self.session.client(
            's3',
            region_name=region,
            endpoint_url=endpoint,
            aws_access_key_id=settings.do_access_key,
            aws_secret_access_key=settings.do_secret
        )
        self.bucket = settings.do_bucket

    async def upload_file(self, file_content: bytes, filename: str, content_type: str) -> str:
        """Uploads a file to DO Spaces and returns the public URL."""
        # Clean filename and add unique prefix
        ext = os.path.splitext(filename)[1]
        unique_filename = f"products/{uuid.uuid4()}{ext}"

        try:
            print(f"Uploading {unique_filename} to bucket {self.bucket}...")
            
            # Using upload_fileobj as it is more robust with ExtraArgs for ACL
            self.client.upload_fileobj(
                io.BytesIO(file_content),
                self.bucket,
                unique_filename,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': content_type
                }
            )
            
            # Verify upload and check ACL
            try:
                self.client.head_object(Bucket=self.bucket, Key=unique_filename)
                print(f"Successfully verified upload of {unique_filename}")
                
                # Check ACL specifically
                acl = self.client.get_object_acl(Bucket=self.bucket, Key=unique_filename)
                print(f"Object ACL for {unique_filename}: {acl.get('Grants')}")
                
                # Verify public-read grant exists
                public_read_exists = any(
                    grant.get('Grantee', {}).get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers' and
                    grant.get('Permission') in ['READ', 'FULL_CONTROL']
                    for grant in acl.get('Grants', [])
                )
                if public_read_exists:
                    print(f"CONFIRMED: {unique_filename} has public-read permissions.")
                else:
                    print(f"WARNING: {unique_filename} does NOT appear to have public-read permissions in its ACL!")
                    
            except Exception as e:
                print(f"Verification FAILED for {unique_filename}: {e}")
                raise Exception(f"Upload verification failed: {str(e)}")

            # Construct the public URL correctly
            endpoint = settings.do_endpoint.rstrip('/')
            if '://' in endpoint:
                scheme, host = endpoint.split('://')
                
                # If host is like "bucket.region.digitaloceanspaces.com" and bucket is "bucket"
                if host.startswith(f"{self.bucket}."):
                    url = f"{scheme}://{host}/{unique_filename}"
                else:
                    url = f"{scheme}://{self.bucket}.{host}/{unique_filename}"
            else:
                url = f"{endpoint}/{self.bucket}/{unique_filename}"
            
            print(f"Generated public URL: {url}")
            return url
        except ClientError as e:
            print(f"Error uploading to DO Spaces: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")

storage_service = StorageService()

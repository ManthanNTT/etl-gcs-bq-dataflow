import json

from google.cloud import storage

class configParser:
    def __init__(self):
        self.storage_client = storage.Client()

    def readConfig(self,bucketName, filename):
        bucket = self.storage_client.get_bucket(bucketName)
        blob = bucket.blob(filename)
        content = blob.download_as_string()
        json_object = json.loads(content)
        return json_object

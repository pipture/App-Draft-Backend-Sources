from django.db import models
from django.conf import settings
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.core.files.storage import FileSystemStorage
from django.core.files import File
import os

def get_sha1_from_file (content):
    try:
        import hashlib
        h = hashlib.sha1()
        h.update(content.read())
        hash = h.hexdigest()
    except Exception as e:
        return (None, e)
    return (hash, None)

class S3Storage(FileSystemStorage):
    def __init__(self, bucket=None, location=None, base_url=None):
        assert bucket
        if location is None:
            location = settings.MEDIA_ROOT
        if base_url is None:
            base_url = settings.MEDIA_URL
        self.location = os.path.abspath(location)
        self.bucket = bucket
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        class S3File(File):
            def __init__(self, key):
                self.key = key
            
            def size(self):
                return self.key.size
            
            def read(self, *args, **kwargs):
                return self.key.read(*args, **kwargs)
            
            def write(self, content):
                self.key.set_contents_from_string(content)
            
            def close(self):
                self.key.close()
                
        return S3File(Key(self.bucket, name))

    def _save(self, name, content):
        
        fileName, fileExtension = os.path.splitext(name)
           
        sha1_hash, error_code = get_sha1_from_file (content)
        if error_code:
            content.close()
            raise error_code
        else:
            name = "%s%s" % (sha1_hash,fileExtension)
        
        key = Key(self.bucket, name)
        if hasattr(content, 'temporary_file_path'):
            content = content.temporary_file_path()
            key.set_contents_from_filename(content)
        elif isinstance(content, File):
            key.set_contents_from_file(content)
        else:
            key.set_contents_from_string(content)
        key.make_public()

        return name

    def delete(self, name):
        self.bucket.delete_key(name)

    def exists(self, name):
        return Key(self.bucket, name).exists()

    def listdir(self, path):
        return [key.name for key in self.bucket.list()]

    def path(self, name):
        raise NotImplementedError

    def size(self, name):
        return self.bucket.get_key(name).size

    def url(self, name):
        return Key(self.bucket, name).generate_url(100000)
    
    def get_available_name(self, name):
        return name
        

class S3EnabledFileField(models.FileField):
    def __init__(self, bucket=settings.DEFAULT_BUCKET, verbose_name=None, name=None, upload_to='', storage=None, **kwargs):
        if settings.USE_AMAZON_S3:
            self.connection = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
            if not self.connection.lookup(bucket):
                self.connection.create_bucket(bucket)
            self.bucket = self.connection.get_bucket(bucket)
            storage = S3Storage(self.bucket)
        super(S3EnabledFileField, self).__init__(verbose_name, name, upload_to, storage, **kwargs)  
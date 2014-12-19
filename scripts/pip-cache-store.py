#!/usr/bin/env python
from boto.s3.connection import S3Connection
from boto.exception import S3ResponseError
import os
from path import path
import sys
import tarfile


class S3TarStore():
    """
    Static methods for storing directories in S3 in tar.gz form.
    """
    @staticmethod
    def bucket(bucket_name):
        """
        Returns bucket matching name. If there exists no such bucket
        or there is a permissions error, then `None` is returned.
        Any other exceptions, uncluding connection errors will be
        raised to be handled elsewhere.
        """
        try:
            conn = S3Connection()
            bucket = conn.get_bucket(bucket_name)
            return bucket
        except S3ResponseError:
            print ( 
                "Please check that the bucket {} exist and that you have "
                "the proper credentials to access it.".format(bucket_name)
            )
            return None

    @staticmethod
    def download_dir(bucket, tarpath, dirpath):
        """
        Downloads a file matching `tarpath.basename()` item from `bucket`
        to `tarpath`. It then extracts the tar.gz file into `dirpath`.
        If no matching tar.gz file is found, it does nothing.
        """
        tarname = tarpath.basename()
        key = bucket.lookup(tarname)
        if key:
            print "Downloading contents of {} from S3.".format(tarname)
            key.get_contents_to_filename(tarpath)

            with tarfile.open(tarpath, mode="r:gz") as tar:
                print "Unpacking {} to {}".format(tarpath, dirpath)
                tar.extractall(path=dirpath.parent)
        else:
            print (
                "Couldn't find anything matching {} in S3 bucket. "
                "Doing Nothing.".format(tarname)
            )

    @staticmethod
    def upload_dir(bucket, tarpath, dirpath):
        """
        Packs the contents for dirpath into a tar.gz file named
        `tarpath.basename()`. It then uploads the tar.gz file to `bucket`.
        If `dirpath` is not a directory, it does nothing.
        """
        tarname = tarpath.basename()

        if dirpath.isdir():
            with tarfile.open(tarpath, "w:gz") as tar:
                print "Packing up {} to {}".format(dirpath, tarpath)
                tar.add(dirpath, arcname=dirpath.basename())

            print "Uploading {} to S3 bucket.".format(tarname)
            existing_key = bucket.lookup(tarname)
            key = existing_key if existing_key else bucket.new_key(tarname)
            key.set_contents_from_filename(tarpath)
        else:
            "Path {} isn't a directory. Doing Nothing.".format(dirname)


class PipCacheStore(S3TarStore):
    """
    Fucntionality for using s3 to cache edx-platform python dependencies for
    jenkins workers.

    Optional environment variables:

    * PIP_CACHE_ID: Will be appended to the name of the expected or created tar files.
      This defaults to 'master'.
    * PIP_DOWNLOAD_CACHE_BUCKET: The name of the bucket where tar files containing
      `~/.pip/download-cache` directories are stored. Default is 'pip-download-caches'.
    * PIP_ACCEL_DATA_DIR_BUCKET: The name of the bucket where tar files containing
      `~/.pip-accel` directories are stored. Default is 'pip-accel-data-dirs'.
    """
    home_dir = path(os.path.expanduser('~'))
    pip_cache_id = os.environ.get('PIP_CACHE_ID', 'master')

    stored_dirs = [
        {
            'path': home_dir / '.pip-accel',
            'tarpath': home_dir / 'pip-accel-data-dir-{}.tar.gz'.format(pip_cache_id),
            'bucket': os.environ.get('PIP_ACCEL_DATA_DIR_BUCKET', 'pip-accel-data-dirs'),
        },
        {
            'path': home_dir / '.pip/download-cache',
            'tarpath': home_dir / 'pip-download-cache-{}.tar.gz'.format(pip_cache_id),
            'bucket': os.environ.get('PIP_DOWNLOAD_CACHE_BUCKET', 'pip-download-caches'),
        },
    ]

    @classmethod
    def download(cls):
        """
        Downloads each of the expected stored directories.
        """
        cls.do_action_for_each(cls.download_dir)

    @classmethod
    def upload(cls):
        """
        Uploads each of the expected stored directories.
        """
        cls.do_action_for_each(cls.upload_dir)

    @classmethod
    def do_action_for_each(cls, action):
        """
        Iterates over `stored_dirs` and performs given action
        on each. Action is either S3TarStore.upload_item or
        S3TarStore.download_item.
        """
        for d in cls.stored_dirs:
            try:
                bucket = cls.bucket(d['bucket'])
            except Exception as e:
                print (
                    "There was an error while connecting to S3. "
                    "Please check error log for more details."
                )
                sys.stderr.write(e.message)
                return 

            if not bucket:
                print "No such bucket {}. Moving on.".format(bucket)
                continue

            dirpath = d['path']
            tarpath = d['tarpath']

            action(bucket, tarpath, dirpath)


def main(action):
    """
    Calls PipCacheStore.upload, PipCacheStore.download or returns
    help text.
    """
    if action in ('u', 'upload', '-u', '--upload'):
        PipCacheStore.upload()
    elif action in ('d', 'download', '-d', '--download'):
        PipCacheStore.download()
    elif action in ('h', 'help', '-h', '--help'):
        print help_text()
    else:
        raise Exception('Invalid option: {}\n'.format(action) + help_text())


def help_text():
    """
    Returns help text for main script.
    """
    return (
        'The following actions are available:'
        '\n\tdownload, d: Downloads the master pip-cache and pip-accel-cache from S3'
        '\n\tupload, u: Uploads the current pip-cache and pip-accel-cache to S3'
        '\n\thelp, h: print this help text'
        '\n\nNote that you must have AWS access and the proper permissions to use this,'
        'and that you may have the permissions to complete all, part, or none of these actions.'
    )


if __name__ == '__main__':
    try:
        action = sys.argv[1].strip()
    except IndexError:
        raise Exception('No option specified.\n' + help_text())
    
    main(action)

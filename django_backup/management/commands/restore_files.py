import os
from optparse import make_option
from tempfile import gettempdir

from django.core.management.base import BaseCommand
from django.conf import settings

import pysftp

from backup import is_media_backup

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--sftp', '-f', action='store_true', default=False, dest='sftp',
            help='Restore media dir using sftp'),
    )

    def handle(self, *args, **options):
        self.remote_dir = settings.RESTORE_FROM_FTP_DIRECTORY or ''
        self.ftp_server = settings.BACKUP_FTP_SERVER
        self.ftp_username = settings.BACKUP_FTP_USERNAME
        self.ftp_password = settings.BACKUP_FTP_PASSWORD

        self.dest_temp_dir = gettempdir()

        connection = self.get_connection()

        backups = [i.strip() for i in connection.sftp_client.listdir(self.remote_dir)]

        media_backups = filter(is_media_backup, backups)
        media_backups.sort()
        media_remote = media_backups[-1]

        media_local = os.path.join(self.dest_temp_dir, media_remote)
        connection.get(os.path.join(self.remote_dir, media_remote), media_local)
        uncompress = self.uncompress(self.dest_temp_dir, media_local)
        if uncompress == 0:
            backup_media_dir = self.get_media_dir_path(self.dest_temp_dir)
            if backup_media_dir:
                self.replace_media(settings.MEDIA_ROOT, backup_media_dir)

    def get_connection(self):
        return pysftp.Connection(host=self.ftp_server, username=self.ftp_username, password=self.ftp_password)

    def uncompress(self, local_path, file):
        cmd = u'tar -C %s -xzf %s' % (local_path, file)
        print '\t', cmd
        return os.system(cmd)

    def get_media_dir_path(self, path):
        media_path = None
        for root, dir_names, file_names in os.walk(path):
            for dir_name in dir_names:
                if dir_name == 'media':
                    media_path = os.path.join(root, dir_name)
                    break
        return media_path

    def replace_media(self, local_path, backup_dir):
        cmd = u'mv -f %s/* %s' % (backup_dir, local_path)
        print '\t', cmd
        os.system(cmd)

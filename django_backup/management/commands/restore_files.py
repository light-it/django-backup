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

        backups = [i.strip() for i in connection.execute('ls %s' % (self.remote_dir))]
        media_backups = filter(is_media_backup, backups)
        media_backups.sort()
        media_remote = media_backups[-1]

        media_local = os.path.join(self.tempdir, media_remote)
        connection.get(os.path.join(self.remote_dir, media_remote), media_local)
        self.uncompress_media(media_local)

    def get_connection(self):
        return pysftp.Connection(host=self.ftp_server, username=self.ftp_username, password=self.ftp_password)

    def uncompress_media(self, file):
        cmd = u'tar -C %s -xzf %s' % (settings.MEDIA_ROOT, file)
        print u'\t', cmd
        os.system(cmd)

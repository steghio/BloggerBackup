# BloggerBackup
Command line script to backup Blogger posts

This script allows users to quickly download posts from their Blogger blog in order to keep a backup copy. On Windows there is the amazing BloggerBackupUtility https://bloggerbackup.codeplex.com/ but sadly that's not available for Linux as well, hence this small project comes to life. It requires Python 3.

Usage is:

        bloggerbackup --api-key <API key> --blog <blog URL> --backup-dir <backup directory> [--start-date <date>] [--end-date <date>] [--verbose]

options:

        --help - prints this help
        
        --api-key <api key> - mandatory API key used to issue queries

        --blog <blog URL> - mandatory URL of the blog to operate on

        --backup-dir <backup directory> - mandatory directory where to put the posts backup

        --start-date <date> - optional, date from which to begin fetching posts in RFC 3339 format: yyyy-MM-ddTHH:mm:ss+HH:mm

        --end-date <date> - optional, date where to stop fetching posts in RFC 3339 format: yyyy-MM-ddTHH:mm:ss+HH:mm

        --verbose - optional, prints debug information while processing
        
The script is extremely barebone and definitely improvable. Also, it requires you to setup an own API key in order to issue queries in the free tier. To do so, visit https://console.developers.google.com/apis/credentials

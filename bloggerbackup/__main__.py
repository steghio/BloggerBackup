import sys, json, validators, os
from nap.url import Url
from dateutil.parser import parse

#global
argin = []
conf = {}

#constants
usage_string = ' Usage: bloggerbackup --help'

def send_request(req):
    '''Sends a GET request and returns the JSON response content'''

    if conf['verbose']:
        print('Sending request: ' + req)

    response = Url(req).get().json()

    if conf['verbose']:
        print('Got response: ' + json.dumps(response))

    return response

def parse_input():
    '''Parses the input arguments from command line
    and sets local variables'''

    #get input
    global argin
    argin = sys.argv

    if '--verbose' in argin:
        conf['verbose'] = True
    else:
        conf['verbose'] = False

    init()

def get_arg_value(arg, is_optional):
    '''Checks wheter a specific argument is set and its value is present'''
    global conf

    #find the arg flag
    try:
        arg_idx = argin.index(arg)
    except:
        #if it is optional argument, set to None and skip finding the value
        if is_optional:
            if conf['verbose']:
                print('Skipping missing optional argument: ' + arg)

            conf[arg[2:]] = None
            return
        else:
            print('No argument: ' + arg + ' found.' + usage_string)
            sys.exit(-1)

    #if we have the arg flag, find the value (should be immediately after us)
    if len(argin) - 1 < arg_idx + 1:
         print('No value found for: ' + arg + usage_string)
         sys.exit(-1)
    #if all is structurally nice, store the value. Finer checks are done in caller functions
    else:
        #store the value without the starting --
        conf[arg[2:]] = argin[arg_idx + 1]


def init():
    '''Initialises local variables'''

    get_api_key()
    get_backup_dir()
    get_blog_url()
    get_posts_link()
    get_start_date()
    get_end_date()

def get_api_key():
    '''Gets the API key needed to query data'''

    if conf['verbose']:
        print('Getting API key')

    get_arg_value('--api-key', False)

def get_backup_dir():
    '''Checks if the desired backup directory is available and usable
    If it does not exist, it creates it'''

    if conf['verbose']:
        print('Setting up backup directory')

    get_arg_value('--backup-dir', False)

    if not os.path.exists(conf['backup-dir']):
        try:
            os.makedirs(conf['backup-dir'])
        except os.error:
            print('Specified backup directory cannot be created.' + usage_string)
            sys.exit(-1)
    else:
        if os.path.isfile(conf['backup-dir']):
            print('Specified backup directory is a file.' + usage_string)
            sys.exit(-1)

def get_blog_url():
    '''Gets the blog URL we will query for data'''

    if conf['verbose']:
        print('Validating input blog URL')

    get_arg_value('--blog', False)

    if not validators.url(conf['blog']):
        print('Incorrect blog URL.' + usage_string)
        sys.exit(-1)

def get_start_date():
    '''Gets the start date filter for the query'''

    if conf['verbose']:
        print('Validating input start date')

    get_arg_value('--start-date', True)

    if conf['start-date'] is not None:
        try:
           parse(conf['start-date'])
        except ValueError:
            print('Incorrect start date format, should be yyyy-MM-ddTHH:mm:ss+HH:mm' + usage_string)
            sys.exit(-1)

def get_end_date():
    '''Gets the end date filter for the query'''

    if conf['verbose']:
        print('Validating input end date')

    get_arg_value('--end-date', True)

    if conf['end-date'] is not None:
        try:
           parse(conf['end-date'])
        except ValueError:
            print('Incorrect end date format, should be yyyy-MM-ddTHH:mm:ss+HH:mm' + usage_string)
            sys.exit(-1)

def get_posts_link():
    '''Gets the link to query the posts of the specified blog if we already do not have it
    From blog_url we get: posts{..., selfLink} and will use selfLink as base for next requests'''
    global conf

    if conf['verbose']:
        print('Getting posts query link')

    response = send_request('https://www.googleapis.com/blogger/v3/blogs/byurl?url=' + conf['blog'] + '&fields=posts&key=' + conf['api-key'])

    if 'error' in response:
        print('Error: ' + json.dumps(response))
        sys.exit(-1)

    if 'posts' not in response:
        print('Blog not found.' + usage_string)
        sys.exit(-1)
    else:
        conf['posts_link'] = response['posts']['selfLink']
        if conf['posts_link'] is None:
            print('No posts link found for blog URL: ' + conf['blog'])
            sys.exit(-1)
        else:
            if not validators.url(conf['posts_link']):
                print('Invalid posts link retrieved: ' + conf['posts_link'])
                sys.exit(-1)

def store_posts(items):
    '''Stores the retrieved posts to disk
    If they are already present, will overwrite them'''

    for item in items:
        store_post(item)

def store_post(item):
    '''Saves a single post to disk'''

    if conf['verbose']:
        print('Storing post: ' + item['title'])

    #create filename including path and strips filename from forbidden characters
    filename = item['published'] + item['title']
    path = os.path.join(conf['backup-dir'], ''.join([x if x.isalnum() else "_" for x in filename]) + '.json')

    file = open(path, 'w')
    json.dump(item, file)
    file.close()

def get_posts():
    '''Queries the posts_link repeatedly to download all posts that match the filter criteria
    and stores them each in a single file in backup_dir with name: <published_date>-<post_title>.json

    Structure is:
    {items = [posts_array], nextPageToken}

    and posts_array is:

    {url, author{author_data}, title, content, published (date), updated (date), labels = [labels_array (strings)]}

    and author_data is:

    {url, id, displayName, image{url}}
    '''

    if conf['verbose']:
        print('Downloading posts')

    #first request will ask for the continuation token since at most 20 posts are returned
    req = conf['posts_link'] + '?fetchImages=true&orderBy=published&status=live&fields=items(author%2Ccontent%2Cimages%2Clabels%2Cpublished%2Ctitle%2CtitleLink%2Cupdated%2Curl)%2CnextPageToken&key=' + conf['api-key']

    #add, if any, start date and end date filters with special characters as HTML entities
    if conf['start-date'] is not None:
        req = req + '&startDate=' + conf['start-date'].replace('-', '%2D').replace(':', '%3A').replace('+', '%2B')

    if conf['end-date'] is not None:
        req = req + '&endDate=' + conf['end-date'].replace('-', '%2D').replace(':', '%3A').replace('+', '%2B')

    response = send_request(req)

    if 'error' in response:
        print('Error: ' + json.dumps(response))
        sys.exit(-1)

    #store each post to disk
    store_posts(response['items'])

    #next requests will pass the continuation token until we reach the end of the stream
    req = req + '&pageToken='

    while 'nextPageToken' in response:

        if conf['verbose']:
            print('Getting next page')

        #prepares and sends the next request by appending the new pageToken we received
        next_req = req + response['nextPageToken']
        response = send_request(next_req)

        if 'error' in response:
            print('Error: ' + json.dumps(response))
            sys.exit(-1)

        #store each post to disk
        store_posts(response['items'])

if __name__ == '__main__':

    if '--help' in sys.argv:
        print("""Usage: bloggerbackup --api-key <api key> --blog <blog URL> --backup-dir <backup directory> [--start-date <date>] [--end-date <date>] [--verbose]

        options:

        --help - prints this help

        --api-key <api key> - mandatory API key used to issue queries

        --blog <blog URL> - mandatory URL of the blog to operate on

        --backup-dir <backup directory> - mandatory directory where to put the posts backup

        --start-date <date> - optional, date from which to begin fetching posts in RFC 3339 format: yyyy-MM-ddTHH:mm:ss+HH:mm

        --end-date <date> - optional, date where to stop fetching posts in RFC 3339 format: yyyy-MM-ddTHH:mm:ss+HH:mm

        --verbose - optional, prints debug information while processing
        """)
        sys.exit(0)

    parse_input()

    get_posts()
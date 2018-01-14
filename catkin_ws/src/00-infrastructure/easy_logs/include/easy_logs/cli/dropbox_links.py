import hashlib
import os
import sys
import urllib
import urlparse

from ruamel import yaml
import ruamel.yaml

import duckietown_utils as dtu
from easy_logs import get_easy_logs_db


def dropbox_links_main(query):
    if len(sys.argv) < 4:
        msg = """

dropbox-links  ~/Dropbox "*.bag" my.urls.yaml

        """
    base = sys.argv[1]
    pattern = sys.argv[2]
    output = sys.argv[3]

    # dtu.get_urls_path()
    if os.path.exists(output):
        urls = yaml.load(open(output).read(), Loader=ruamel.yaml.Loader)
        for k, v in list(urls.items()):
            if not v.startswith('http'):
                del urls[k]
    else:
        urls = {}
    command = 'dropbox'

    files = dtu.locate_files(base, pattern, normalize=False)
    print('base: %s found %d' % (base, len(files)))
    for filename in files:
        if '.dropbox.cache' in filename:
            continue
        logname = os.path.basename(filename)
        if logname in urls:
            dtu.logger.info('Already have %s' % logname)
            continue

        #filename = log.filename
        #only = filename.replace(base, '')

        only = filename
        cmd = [command, 'sharelink', only]
        res = dtu.system_cmd_result(cwd='.', cmd=cmd,
                      display_stdout=False,
                      display_stderr=True,
                      raise_on_error=True,
                      write_stdin='',
                      capture_keyboard_interrupt=False,
                      env=None)
        link = res.stdout.strip()
        if 'unknown error' in link.lower():
            msg = 'Could not get link: %s' % link
            raise Exception(msg)
        link = link.replace('dl=0', 'dl=1')

        if 'responding' in link:
            dtu.logger.debug('Dropbox is not responding, I will stop here.')

            break

        dtu.logger.info('link : %s' % link)
        key = logname
        #key = logname.decode('utf-8')
        #print key#, key.__type__
        urls[key] = link
        url = dtu.create_hash_url(filename)
        urls[url] = link
        dtu.logger.info('url : %s' % url)

    from collections import OrderedDict
    urls_sorted = OrderedDict()
    for k in sorted(urls):
        urls_sorted[k] = urls[k]
    urls = urls_sorted
    yaml.default_flow_style = False
    with open(output, 'w') as f:
        yaml.dump(urls, f, default_flow_style=False, allow_unicode=True)


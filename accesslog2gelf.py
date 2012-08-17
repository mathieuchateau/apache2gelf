#!/usr/bin/env python
import sys
import re
import graypy
import logging
import argparse

# Copyright (c) 2012 Anton Tolchanov <me@knyar.net>
# https://github.com/knyar/apache2gelf

parser = argparse.ArgumentParser(description='Reads apache access log on stdin and delivers messages to graylog2 server via GELF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Add the following to apache virtualhost configuration to use:\n" +
        'CustomLog "||/path/to/accesslog2gelf.py" "%V %h %u \\"%r\\" %>s %b \\"%{Referer}i\\""')
parser.add_argument('--host', dest='host', default='localhost', help='graylog2 server hostname (default: localhost)')
parser.add_argument('--port', dest='port', default='12201', help='graylog2 server port (default: 12201)')
parser.add_argument('--facility', dest='facility', default='access_log', help='logging facility (default: access_log)')
parser.add_argument('--vhost', dest='vhost', help='Add additional "vhost" term to all log records. This can be used to differentiate between virtual hosts.')
args = parser.parse_args()

"""The list of expected fields is hard-coded. Please feel free to change it
As specified above, this requires the following line in apache configuration:

    CustomLog "||/path/to/accesslog2gelf.py" "%V %h %u \"%r\" %>s %b \"%{Referer}i\""

"""
regexp = '^(\S+) (\S+) (\S+) "([^"]*)" (\S+) (\S+) "([^"]*)"$'
fields = 'host ipaddr username request status size referer'.split()

baserecord = {}
if args.vhost:
    baserecord['vhost'] = args.vhost

logger = logging.getLogger(args.facility)
logger.setLevel(logging.DEBUG)
logger.addHandler(graypy.GELFHandler(args.host, int(args.port), debugging_fields=False))

while True:
    line = sys.stdin.readline()
    if not line: break
    matches = re.search(regexp, line)
    if matches:
        record = baserecord
        for i in range(len(fields)):
            record[fields[i]] =  matches.group(i+1)
        adapter = logging.LoggerAdapter(logging.getLogger(args.facility), record)
        """Default output message format is also hard-coded"""
        if args.vhost:
            adapter.info('%s %s (%s) "%s" %s %s "%s"' % (record['ipaddr'], args.vhost, record['host'], record['request'],
                record['status'], record['size'], record['referer']))
        else:
            adapter.info('%s %s "%s" %s %s "%s"' % (record['ipaddr'], record['host'], record['request'],
                record['status'], record['size'], record['referer']))


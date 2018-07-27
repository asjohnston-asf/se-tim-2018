import csv
import os
import re
from io import StringIO
from datetime import datetime

import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth


indexDoc = {
    'dataRecord': {
        'properties': {
            'ip_address':  {'type': 'ip'},
            'datetime':    {'type': 'date'},
            'operation':   {'type': 'string'},
            'file_name':   {'type': 'string'},
            'http_status': {'type': 'long'},
            'bytes_sent':  {'type': 'long'},
            'file_size':   {'type': 'long'},
            'user_id':     {'type': 'string'},
            'request_id':  {'type': 'string'},
        },
    },
    'settings': {
        'number_of_replicas': 0,
        'number_of_shards': 1,
    },
}


def get_log_records(bucket, key):
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket, key).get()
    content = obj['Body'].read().decode('utf-8')
    log_records = csv.reader(StringIO(content), delimiter=' ', quotechar='"')
    return log_records


def get_user_id(request_uri):
    userid_pattern = re.compile(r'&userid=([a-zA-Z0-9\._]+)')
    result = userid_pattern.search(request_uri)
    if result:
        return result.group(1)
    return ''


def to_number(s):
    if s == '-':
        return 0
    return int(s)


def get_elasticsearch_connection(domain_url):
    auth = AWSRequestsAuth(aws_access_key=os.getenv('AWS_ACCESS_KEY_ID'),
                           aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                           aws_token=os.getenv('AWS_SESSION_TOKEN'),
                           aws_host=domain_url,
                           aws_region=os.getenv('AWS_REGION'),
                           aws_service='es')
    es = Elasticsearch(hosts=[{'host': domain_url, 'port': 443}],
                       use_ssl=True,
                       verify_certs=True,
                       http_auth=auth,
                       connection_class=RequestsHttpConnection)
    return es


def process_log_file(bucket, key):
    index = 'myindex'
    records = get_log_records(bucket, key)
    es = get_elasticsearch_connection(os.getenv('ES_HOST'))
    if not es.indices.exists(index):
        es.indices.create(index, body=indexDoc)
    for record in records:
        data = {
            'ip_address': record[4],
            'datetime': datetime.strptime(' '.join(record[2:4]), "[%d/%b/%Y:%H:%M:%S %z]"),
            'request_id': record[6],
            'operation': record[7],
            'file_name': record[8],
            'http_status': to_number(record[10]),
            'bytes_sent': to_number(record[12]),
            'file_size': to_number(record[13]),
            'user_id': get_user_id(record[9]),
        }
        if data['operation'] == 'REST.GET.OBJECT' and data['http_status'] in [200, 206]:
            print(data)
            es.index(index=index, id=data['request_id'], doc_type='log', body=data)


def lambda_handler(event, context):
    for record in event['Records']:
        process_log_file(record['bucket']['name'], record['object']['key'])

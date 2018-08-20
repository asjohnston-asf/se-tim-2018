import json
import os
import boto3
from flask import Flask, redirect, request


app = Flask(__name__)
s3 = boto3.client('s3')


@app.before_first_request
def init_app():
    config = json.loads(os.environ['APP_CONFIG'])
    app.config.update(dict(config))


@app.route('/<path:object_key>')
def download_redirect(object_key):
    signed_url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': app.config['bucket'],
            'Key': object_key,
        },
        ExpiresIn=app.config['expire_time_in_seconds'],
    )
    signed_url = signed_url + '&userid=' + request.environ.get('URS_USERID')
    return redirect(signed_url)

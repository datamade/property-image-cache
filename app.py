from flask import Flask, request, make_response
import json
import requests
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import S3ResponseError
from app_config import AWS_KEY, AWS_SECRET
from io import StringIO, BytesIO

app = Flask(__name__)

@app.route('/<pin>.jpeg')
def index(pin):

    s3_conn = S3Connection(AWS_KEY, AWS_SECRET)
    bucket = s3_conn.get_bucket('property-image-cache')
    s3_key = Key(bucket)
    s3_key.key = '{0}.jpeg'.format(pin)

    try:
        output = BytesIO()
        s3_key.get_contents_to_file(output)
    
    except S3ResponseError:
        
        image_viewer = 'http://cookviewer1.cookcountyil.gov/Jsviewer/image_viewer/requestImg.aspx?{0}='
        image_url = image_viewer.format(pin)
        image = requests.get(image_url)
        
        output = BytesIO(image.content)
        s3_key.set_metadata('Content-Type', 'image/jpeg')
        s3_key.set_contents_from_file(output)
        s3_key.set_acl('public-read')
        
    output.seek(0)
    response = make_response(output.read())
    response.headers['Content-Type'] = 'image/jpeg'
    return response


if __name__ == "__main__":
    import os

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

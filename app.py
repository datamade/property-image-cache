from flask import Flask, request, make_response, abort
import json
import requests
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import S3ResponseError
from app_config import AWS_KEY, AWS_SECRET, SENTRY_DSN
from io import StringIO, BytesIO
from flask_cors import cross_origin

from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__)

LEGISTARS = {
    'chicago': 'https://ord.legistar.com/View.ashx',
    'nyc': 'http://legistar.council.nyc.gov/View.ashx',
}

WHITELIST = ['ord.legistar.com', 'chicago.legistar.com']

from raven.contrib.flask import Sentry
sentry = Sentry(app, dsn=SENTRY_DSN)

@app.route('/<pin>.jpg')
def index(pin):

    s3_conn = S3Connection(AWS_KEY, AWS_SECRET)
    bucket = s3_conn.get_bucket('property-image-cache')
    s3_key = Key(bucket)
    s3_key.key = '{0}.jpg'.format(pin)

    if s3_key.exists():
        output = BytesIO()
        s3_key.get_contents_to_file(output)

    else:
        image_viewer = 'http://www.cookcountyassessor.com/PropertyImage.aspx?pin={0}'
        image_url = image_viewer.format(pin)
        image = requests.get(image_url)
        
        if image.headers['Content-Type'] == 'image/jpeg':
            output = BytesIO(image.content)
            s3_key.set_metadata('Content-Type', 'image/jpg')
            s3_key.set_contents_from_file(output)
            s3_key.set_acl('public-read')
        else:
            sentry.captureMessage('Could not find image for PIN %s' % pin)
            abort(404)
    
    output.seek(0)
    response = make_response(output.read())
    response.headers['Content-Type'] = 'image/jpg'
    return response

@app.route('/<city>/document/')
@cross_origin()
def document(city):
    try:
        query_params = request.url.rsplit('?', 1)[1]
    except IndexError:
        abort(400)
    
    filename, document_url = query_params.split('&', 1)

    if not document_url:
        abort(404)
    
    document_url = unquote(document_url.replace('document_url=', ''))
    filename = unquote(filename.replace('filename=', ''))
    parsed_url = urlparse(document_url)

    if parsed_url.netloc not in WHITELIST:
        abort(400)
    
    parsed_query = parse_qs(parsed_url.query)

    if parsed_query:
        try:
            doc_id = parsed_query['ID'][0]
        except (KeyError, IndexError):
            doc_id = ''

        try:
            guid = parsed_query['GUID'][0]
        except (KeyError, IndexError):
            guid = ''

    else:
        doc_id = ''
        guid = parsed_url.path.rsplit('/')[-1]
    
    if not guid:
        abort(400)

    s3_conn = S3Connection(AWS_KEY, AWS_SECRET)
    bucket = s3_conn.get_bucket('councilmatic-document-cache')
    s3_key = Key(bucket)
    s3_key.key = '{doc_id}_{guid}'.format(doc_id=doc_id, 
                                              guid=guid)

    if s3_key.exists():
        output = BytesIO()
        s3_key.get_contents_to_file(output)
        content_type = s3_key.content_type
        filename = s3_key.metadata['filename']

    else:
        
        doc = requests.get(document_url)
        
        if doc.status_code == 200:
            output = BytesIO(doc.content)
            
            content_type = doc.headers['content-type']

            if doc.headers.get('content-disposition'):
                filename = doc.headers['content-disposition'].rsplit('=', 1)[1].replace('"', '')

            s3_key.set_metadata('content-type', content_type)
            s3_key.set_metadata('filename', filename)
            s3_key.set_contents_from_file(output)
            s3_key.set_acl('public-read')
        
        else:
            sentry.captureMessage('Could not find document at URL %s' % document_url)
            abort(doc.status_code)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = content_type
    
    if 'pdf' not in content_type:
        response.headers['Content-Disposition'] = 'attachment;filename="{}"'.format(filename)

    return response


if __name__ == "__main__":
    import os

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

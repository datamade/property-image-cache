from flask import Flask, request, make_response, abort
import json
import requests
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import S3ResponseError
from app_config import AWS_KEY, AWS_SECRET, SENTRY_DSN, IMAGE_SECRET
from io import StringIO, BytesIO
from flask_cors import cross_origin

from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__)

LEGISTARS = {
    'chicago': 'https://ord.legistar.com/View.ashx',
    'nyc': 'http://legistar.council.nyc.gov/View.ashx',
    'lametro': 'https://metro.legistr.com/View.ashx'
}

WHITELIST = ['ord.legistar.com', 'chicago.legistar.com', 'metro.legistar1.com', 'metro.legistar.com']

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

        if  'image/jpeg' in image.headers['Content-Type']:
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

    query = parse_qs(urlparse(request.url).query)

    if not query:
        abort(400)

    document_url, = query['document_url']
    filename, = query['filename']

    document_url_parsed = urlparse(document_url)

    if document_url_parsed.netloc not in WHITELIST:
        abort(400)

    document_query = parse_qs(document_url_parsed.query)

    doc_id, = document_query.get('ID', (None,))
    guid, = document_query.get('GUID',
                               (document_url_parsed.path.rsplit('/')[-1],))

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
        source_url = s3_key.metadata.get('source_url', None)

    else:

        doc = requests.get(document_url)
        source_url = doc.url

        if doc.status_code == 200:
            output = BytesIO(doc.content)

            content_type = doc.headers['content-type']

            if doc.headers.get('content-disposition'):
                filename = doc.headers['content-disposition'].rsplit('=', 1)[1].replace('"', '')

            s3_key.set_metadata('content-type', content_type)
            s3_key.set_metadata('filename', filename)
            s3_key.set_metadata('source_url', source_url)
            s3_key.set_contents_from_file(output)
            s3_key.set_acl('public-read')

        else:
            sentry.captureMessage('Could not find document at URL %s' % document_url)
            abort(doc.status_code)

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = content_type
    response.headers['Source URL'] = source_url

    if 'pdf' not in content_type:
        response.headers['Content-Disposition'] = 'attachment;filename="{}"'.format(filename)

    return response

@app.route('/image/')
def image():

    if not request.args.get('key') == IMAGE_SECRET:
        abort(401)

    try:
        image_url = request.args['url']
    except KeyError:
        abort(400)

    parsed_url = urlparse(image_url)

    if not parsed_url.netloc:
        abort(400)

    remote_file = parsed_url.path.rsplit('/', 1)[-1]

    s3_conn = S3Connection(AWS_KEY, AWS_SECRET)
    bucket = s3_conn.get_bucket('myreps-image-cache')
    s3_key = Key(bucket)
    s3_key.key = '{0}/{1}'.format(parsed_url.netloc, remote_file)

    if s3_key.exists():
        output = BytesIO()
        s3_key.get_contents_to_file(output)

    else:

        # For some reason, things hosted on illinois.gov do not have a valid
        # SSL cert, at least according to my humble operating system. The
        # problem is that it redirects to HTTPS and then the cert is not valid.
        # *shrug*

        image = requests.get(image_url, verify=False)

        if image.status_code == 200 and 'image' in image.headers['Content-Type']:
            output = BytesIO(image.content)
            s3_key.set_metadata('Content-Type', 'image/jpg')
            s3_key.set_contents_from_file(output)
            s3_key.set_acl('public-read')

        else:
            sentry.captureMessage('Image does not exist at %s' % image_url)
            abort(404)

    output.seek(0)
    response = make_response(output.read())
    response.headers['Content-Type'] = 'image/jpg'
    return response


if __name__ == "__main__":
    import os

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

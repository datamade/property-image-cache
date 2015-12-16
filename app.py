from flask import Flask, request, make_response, abort
import json
import requests
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import S3ResponseError
from app_config import AWS_KEY, AWS_SECRET
from io import StringIO, BytesIO

app = Flask(__name__)

LEGISTARS = {
    'chicago': 'https://chicago.legistar.com/View.ashx',
    'nyc': 'http://legistar.council.nyc.gov',
}

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
        image_viewer = 'http://cookviewer1.cookcountyil.gov/Jsviewer/image_viewer/requestImg.aspx?{0}='
        image_url = image_viewer.format(pin)
        image = requests.get(image_url)
        
        if image.headers['Content-Type'] == 'image/jpeg':
            output = BytesIO(image.content)
            s3_key.set_metadata('Content-Type', 'image/jpg')
            s3_key.set_contents_from_file(output)
            s3_key.set_acl('public-read')
        else:
            abort(404)
    
    output.seek(0)
    response = make_response(output.read())
    response.headers['Content-Type'] = 'image/jpg'
    return response

@app.route('/<city>/document/')
def document(city):
    doc_id, guid = request.args.get('ID'), request.args.get('GUID')

    if not id or not guid:
        abort(404)
    
    base_url = LEGISTARS.get(city)

    if not base_url:
        abort(404)

    
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
        url = '{base_url}?M=F&ID={doc_id}&GUID={guid}'.format(base_url=base_url,
                                                              doc_id=doc_id,
                                                              guid=guid)
        
        doc = requests.get(url)
        
        if doc.status_code == 200:
            filename = doc.headers['content-disposition'].rsplit(';', 1)[1]
            content_type = doc.headers['content-type']

            output = BytesIO(doc.content)
            s3_key.set_metadata('content-type', content_type)
            s3_key.set_metadata('filename', filename)
            s3_key.set_contents_from_file(output)
            s3_key.set_acl('public-read')
        
        else:
            abort(doc.status_code)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = content_type
    
    if 'pdf' not in content_type:
        response.headers['Content-Disposition'] = 'attachment;{}'.format(filename)

    return response


if __name__ == "__main__":
    import os

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

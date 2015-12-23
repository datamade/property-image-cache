if __name__ == "__main__":
    from boto.s3.connection import S3Connection
    from boto.s3.key import Key
    from app_config import AWS_KEY, AWS_SECRET

    import requests
    import csv
    from hashlib import md5
    import piexif

    from PIL import Image
    from io import BytesIO

    s3_conn = S3Connection(AWS_KEY, AWS_SECRET)
    bucket = s3_conn.get_bucket('property-image-cache')
    s3_key = Key(bucket)
    
    with open('chicago_pins.csv') as f:
        reader = csv.reader(f)
        
        for pin in reader:
            
            s3_key.key = '{0}.jpg'.format(pin[0])
            
            stored_hash = None
            if s3_key.exists():
                stored_string = s3_key.get_contents_as_string()
                stored_hash = md5(stored_string).hexdigest()
            
            image_viewer = 'http://www.cookcountyassessor.com/PropertyImage.aspx?pin={0}'
            image_url = image_viewer.format(pin)
            image = requests.get(image_url)
            
            new_string = image.content
            new_hash = md5(new_string).hexdigest()
            
            print('STORED Image data ######')
            print(Image.open(BytesIO(stored_string)).size)
            print('NEW EXIF ######')
            print(Image.open(BytesIO(new_string)).size)

            print(stored_hash, new_hash, pin)
            print(len(stored_string), len(new_string))

            break

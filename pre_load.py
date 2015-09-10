if __name__ == "__main__":
    import sys
    import requests
    import csv
    import time

    if sys.argv[1] == 'local':
        url_pattern = 'http://127.0.0.1:5000/{0}.jpg'
    else:
        url_pattern = 'https://pic.datamade.us/{0}.jpg'

    with open('chicago_pins.csv') as f:
        reader = csv.reader(f)

        for pin in reader:
            image = requests.get(url_pattern.format(pin[0]))
            print('fetched %s.jpg' % pin[0])
            time.sleep(1)

# Property Image Cache

The one-stop shop for all your cross origin request needs. This README contains only instructions for Councilmatic users.

## A new Councilmatic, you say?

### Property Image Cache

Update LEGISTARS and WHITELIST in `app.py`.

The LEGISTARS variable should point to a city name and the url to its legistar site. The WHITELIST variable should point to the url that appears in the document link. Note: you may need two per city, as in the case of LA Metro.

### Councilmatic

Find the `full_text_doc_url` method, which generates an encoded url that directs to a document or image. To test this locally, the base url should point to your local port:

```
# base_url = 'https://pic.datamade.us/lametro/document/'
base_url = 'http://127.0.0.1:5000/lametro/document/'http://127.0.0.1:5000/lametro/document/
```

### Run it!

```
python app.py
```

Then, go to a Councilmatic page of your chosing, and view your embedded PDF.

When you finish, do not forget to pull your changes onto the "Hotdog Princess" server.



Palvelutori
------------

## Installation (without Docker)

1. Create a virtualenv (e.g. `mkvirtualenv palvelutori -p python3`)
2. Install Python dependencies: `pip install -r requirements.txt`
3. Create a Postgresql database
4. Copy `palvelutori/local_settings.sample` to `palvelutori/local_settings.py` and customize
5. Run `./manage.py migrate` to initialize the database
6. Create an admin account with `./manage.py createsuperuser`

## Installation (using Docker)

TODO

## Testing

Run automatic tests with `./manage.py test`

API usage examples (included in automatic testing) can be found in `examples/curl/`

Swagger documentation can be accessed at <http://localhost:8000/docs/>
and the API itself at <http://localhost:8000/api>.

The admin web interface is at <http://localhost:8000/admin/>


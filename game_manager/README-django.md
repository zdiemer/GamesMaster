# Django tips

## Docker compose commands

Via shell script:

```sh
$ sh init.sh
```

This should run the stack, and then apply all migrations and commit some test data.

When you're done, pull the stack down:

```sh
$ docker compose down
# to reset the db volume as well.
$ docker compose down -v
```


or you can run the server yourself manually.

```sh
$ docker compose build

$ docker compose up
```

### Individual commands

Create an app

```sh
$ sudo docker compose run web python manage.py startapp backend
# set the chown of the new app to be owned by the user
$ ls -l
# look at files not owned by you
$ sudo chown -R $USER:$USER backend
```

Applying migrations.

```sh
$ sudo docker compose run web python manage.py migrate
```

Create superuser.

```sh
$ sudo docker compose run web python manage.py createsuperuser
```

Run scripts

```sh
$ sudo docker compose run web python manage.py runscript test_data
```

```sh
$ sudo docker compose run web python manage.py makemigrations
```
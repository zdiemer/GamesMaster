# Django tips

## Docker compose commands

Run the server yourself locally

```sh
$ docker compose build

$ docker compose up
```

Create an app

```sh
$ sudo docker compose run web python manage.py startapp backend
# set the chown of the new app to be owned by the user
$ ls -l
# look at files not owned by you
$ sudo chown -R $USER:$USER backend
```

Applyting migrations.

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
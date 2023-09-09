# Docker Specifics

## DEV Cmds

```sh
# build the images
$ docker compose -f docker-compose.dev.yaml --env-file ./dev.env build

# view the config
$ docker compose -f docker-compose.dev.yaml --env-file ./dev.env config

# run em'
$ docker compose -f docker-compose.dev.yaml --env-file ./dev.env up

# tear down and remove the mysql volume
$ docker compose -f docker-compose.dev.yaml down -v
```

### MySQL commands

```sh
# get into mysql
$ docker exec -it app-mysql-1 bash
$ mysql -u root -p

# read some data
mysql> show databases;                                                                                                                                     
+--------------------+                                                                                                                                     
| Database           |                                                                                                                                     
+--------------------+                                                                                                                                     
| GamesMaster        |                                                                                                                                     
| information_schema |                                                                                                                                     
| mysql              |                                                                                                                                     
| performance_schema |                                                                                                                                     
| sys                |                                                                                                                                     
+--------------------+                                                                                                                                     
5 rows in set (0.01 sec) 

mysql> use GamesMaster;                                                                                                                                          
Database changed     

mysql> select * from games;                                                                                                                                      
+--------------------------------------+--------------+                                                                                                          
| game_id                              | title        |                                                                                                          
+--------------------------------------+--------------+                                                                                                          
| 68e24c66-e25c-46fe-a97e-b5e0fe37124b | Test Game #1 |                                                                                                          
+--------------------------------------+--------------+                                                                                                          
1 row in set (0.01 sec)                                                                                                                                          
```

(You can enter `exit` twice to get out of mysql & the bash terminal.)

### Adminer

Adminer is a basic webapp used to inspect databases. Access it by going to `http://localhost:8095` (or whatever is in you `dev.env` as the `DB_ADMINER_PORT`).

The dev default credentials are:
* server: mysql (the name of the db container)
* username: root
* password: 1234

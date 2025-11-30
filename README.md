# UberStrike Discord Bots

## Start Containeir
```
docker compose up --build -d
```

## Commands
The docker compose uses volumes which persist container restart/server reboot.
Deleting a docker container does not delete a Docker Volume.

- List docker containers
```
docker ps
```

- Delete docker container
```
docker rm -f <container_name>
```

- List docker volumes
```
docker volume ls
```

- Delete docker volume
```
docker volume rm <volume_name>
```


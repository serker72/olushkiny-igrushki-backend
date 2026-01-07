## Разворачивание проекта

Описано в файле `README.md` репозитория `levelcraft-services`


# Создание пользователя MinIO
- подключиться к контейнеру в терминале
```shell
docker exec -it olushkiny-igrushki-minio bash
```
- получить список алиасов
```shell
mc alias list
```
- сгенерировать `access_key` и `secret_key`
```shell
# access_key
openssl rand -hex 16
# secret_key
openssl rand -base64 32
```
- установить алиас `local`
```shell
mc alias set local http://127.0.0.1:9000 {MINIO_USERNAME} {MINIO_PASSWORD}
```
- создать пользователя
```shell
# mc admin user add ALIAS ACCESSKEY SECRETKEY
mc admin user add local {access_key} {secret_key}
```
- добавить в файл `.env` параметры:
```
```
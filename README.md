# Church Class List

When syncing [Member Tools](https://apps.apple.com/us/app/lds-tools/id391093033), it includes class information in the membership data.  However, it doesn't allow me to see the class membership under Organizations.

I'm assuming this is a bug as I can see class information for individual members in the Directory.

This project retrieves the data and outputs the members of the class you enter.  It can be run in Docker or on iOS with [Pythonista](https://omz-software.com/pythonista/).

## Building

Set your unit number in `church_class_list/config.json`

```yaml
---
unit: 000000 # Int: Your unit number
```

```shell
docker build . --tag church-class-list:latest
```

## Running

You will need the CLIENT_ID and CLIENT_SECRET for Member Tools to perform the OAuth.  Place them into `.docker_env` in the root of this repo.

Do not place quotes around the values in this file.

```
CHURCH_CLASS_OAUTH_CLIENT_ID=*****************
CHURCH_CLASS_OAUTH_CLIENT_SECRET=*****************
```

Alernatively, if you are running this in [Pythonista](http://omz-software.com/pythonista/) you can save them to the Pythonista `keystore`.

```python
keychain.set_password("lds", "oauth_client_id", "*****************")
keychain.set_password("lds", "oauth_client_secret", "*****************")
```

```shell
mkdir data

docker run -it \
  --mount type=bind,source=`pwd`/church_class_list/config.yml,target=/app/config.yml \
  --mount type=bind,source=`pwd`/data,target=/app/data \
  --env-file=.docker_env church-class-list:latest
```

It will prompt you for your credentials, organization and class and save a list of class members in `data/class_members.txt`.

The organization and class need to match what is in Member Tools.

It will also save a cache in `data/membertools_data.json` and will use that for future runs.  Delete it if you wish to download fresh data.

import json
import os
from getpass import getpass

import requests
import yaml

try:
    # These will import when running in Pythonista
    import dialogs
    import keychain

    pythonista = True
except ImportError:
    pythonista = False

membertools_data_cache = "data/membertools_data.json"


def search(data: list, key: str, value) -> list:
    return list(filter(lambda x: x[key] == value, data))


def get_credentials() -> dict:
    if pythonista is True:
        username, password = dialogs.login_alert("LDS Credentials")
    else:
        try:
            username = os.environ["CHURCH_CLASS_USERNAME"]
        except KeyError:
            username = input("Username: ")
        except Exception as e:
            raise e

        try:
            password = os.environ["CHURCH_CLASS_PASSWORD"]
        except KeyError:
            password = getpass(prompt="Password: ")
        except Exception as e:
            raise e

    return {
        "username": username,
        "password": password,
    }


def get_class() -> dict:
    if pythonista is True:
        organization = dialogs.input_alert("Organization")
        org_class = dialogs.input_alert("Class")
    else:
        organization = input("Organization: ")
        org_class = input("Class: ")

    return {
        "organization": organization,
        "class": org_class,
    }


def get_oauth2_credentials() -> dict:
    if pythonista is True:
        client_id = keychain.get_password("lds", "oauth_client_id")
        client_secret = keychain.get_password("lds", "oauth_client_secret")
    else:
        client_id = os.environ["CHURCH_CLASS_OAUTH_CLIENT_ID"]
        client_secret = os.environ["CHURCH_CLASS_OAUTH_CLIENT_SECRET"]

    return {
        "client_id": client_id,
        "client_secret": client_secret,
    }


def get_class_uuid(organization: dict, name: str) -> str:
    try:
        organization_class = search(
            data=organization["childOrgs"], key="name", value=name
        )

        if isinstance(organization_class, list) and len(organization_class) == 1:
            return organization_class[0]["uuid"]
    except Exception as e:
        raise SystemExit(e)

    raise SystemExit("Class or Organization Not Found")


def get_oauth2_id_token(data: dict) -> str:
    try:
        r = requests.post(
            "https://ident.churchofjesuschrist.org/sso/oauth2/access_token",
            data=data,
        )
    except Exception as e:
        raise SystemExit(e)

    return r.json()["id_token"]


def get_mobile_auth(auth_headers: dict, username: str, password: str) -> dict:
    try:
        json = {
            "username": username,
            "password": password,
        }

        r = requests.post(
            "https://mobileauth.churchofjesuschrist.org/v1/mobile/login",
            headers=auth_headers,
            json=json,
        )
    except Exception as e:
        raise SystemExit(e)

    return r.json()


def get_membertools_cache(cache: str) -> dict:
    try:
        with open(cache, "r") as f:
            return json.loads(f.read())
    except FileNotFoundError:
        return {}
    except Exception as e:
        raise e


def save_membertools_cache(membertools_data: dict, cache: str):
    with open(cache, "w") as f:
        json.dump(membertools_data, f, indent=2)


def get_membertools_data(unit: int, auth_headers: dict, cookies: dict):
    json_data = [
        {
            "types": ["HOUSEHOLDS", "ORGANIZATIONS"],
            "unitNumbers": [unit],
        }
    ]

    r = requests.post(
        "https://wam-membertools-api.churchofjesuschrist.org/api/v4/sync?force=true",
        json=json_data,
        headers=auth_headers,
        cookies=cookies,
    )

    membertools_data = r.json()

    save_membertools_cache(
        membertools_data=membertools_data, cache=membertools_data_cache
    )

    return membertools_data


def get_unit_household_members(households: list) -> list:
    return [
        member
        for members in [household["members"] for household in households]
        for member in members
    ]


def get_class_members(households: list, uuid: str):
    members = list(
        filter(
            lambda member: uuid in member.get("classes", []),
            get_unit_household_members(households=households),
        )
    )

    return sorted(members, key=lambda member: member["displayName"])


def main():
    with open("config.yml", "r") as f:
        config = yaml.safe_load(f.read())

    oauth2_credentials = get_oauth2_credentials()

    membertools_data = get_membertools_cache(cache=membertools_data_cache)

    if not isinstance(membertools_data, dict) or membertools_data == {}:
        oauth2_data = {
            "grant_type": "client_credentials",
            "client_id": oauth2_credentials["client_id"],
            "client_secret": oauth2_credentials["client_secret"],
            "scope": "openid profile",
        }

        bearer = get_oauth2_id_token(data=oauth2_data)

        auth_headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Authorization": f"Bearer {bearer}",
        }

        credentials = get_credentials()

        mobile_auth_data = get_mobile_auth(
            auth_headers=auth_headers,
            username=credentials["username"],
            password=credentials["password"],
        )

        membertools_cookies = {mobile_auth_data["name"]: mobile_auth_data["value"]}

        membertools_data = get_membertools_data(
            unit=config["unit"], auth_headers=auth_headers, cookies=membertools_cookies
        )

    class_search = get_class()

    organization_name = class_search["organization"]
    class_name = class_search["class"]

    organization = search(
        data=membertools_data["organizations"],
        key="name",
        value=organization_name,
    )

    if len(organization) != 1:
        raise SystemExit("Too many organizations returned")

    if class_name == "":
        uuid = organization[0]["uuid"]
    else:
        uuid = get_class_uuid(
            organization=organization[0], name=class_name
        )

    with open("data/class_members.txt", "w", encoding="utf-8") as f:
        for member in get_class_members(
            households=membertools_data["households"], uuid=uuid
        ):
            f.write(f"{member['preferredName']}\n")


if __name__ == "__main__":
    main()

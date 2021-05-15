from objhook import hook_by_name, objhook, Typed
from typing import Final
from http.cookies import SimpleCookie
import requests


@hook_by_name
class Address:
    address: str
    city: str
    country: str
    district: str
    formatted_address: Typed(str, "formattedAddress")
    full_address: str
    geo_string: Typed(str, "geoString")
    id: int
    name: str
    phone: str
    state: str
    town: str
    zipcode: int


@hook_by_name
class User:
    userid: int
    shopid: int
    username: str
    email: str
    phone: str
    phone_verified: bool
    default_address: Address
    cookie: str
    csrf_token: str

    @staticmethod
    def login(cookie: str):
        resp = requests.get(
            "https://shopee.vn/api/v1/account_info",
            headers={
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://shopee.vn/",
                "Cookie": cookie
            }
        )
        data = resp.json()

        if len(data) == 0:
            raise Exception("failed to login, invalid cookie")

        data["cookie"] = cookie
        data["csrf_token"] = SimpleCookie(cookie).get("csrftoken").value

        return objhook(User, data)

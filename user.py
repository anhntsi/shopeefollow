from objhook import by_name, objhook, Typed, Class
from typing import Final
from requests.cookies import RequestsCookieJar
import requests


@by_name
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


@by_name
class User:
    userid: int
    shopid: int
    username: str
    email: str
    phone: str
    phone_verified: bool
    default_address: Class(Address, "default_address")
    cookie: RequestsCookieJar
    csrf_token: str

    def login(cookie: RequestsCookieJar):
        resp = requests.get(
            "https://shopee.vn/api/v1/account_info",
            headers={
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://shopee.vn/"
            },
            cookies=cookie
        )
        data = resp.json()

        if len(data) == 0:
            raise Exception("failed to login, invalid cookie")

        data["csrf_token"] = cookie.get("csrftoken")

        user = objhook(User, data)
        user.cookie = cookie

        return user

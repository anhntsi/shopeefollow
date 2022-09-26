from typing import Final, Union
import user
import requests
from http.cookies import SimpleCookie
from typing import List
from shopdata import Shop
from objhook import objhook
import bs4


class Follower:
    shopid: int
    userid: int
    username: str
    name: str

    def __init__(self, soup: bs4.BeautifulSoup = None, data: dict = None):
        print('Test', data)
        if data is not None:
            self.shopid = data["shopid"]
            self.userid = data["userid"]
            self.username = data["username"]
            self.name = data["shopname"]
            return

        a1 = soup.find_all("a")

        if len(a1) < 3:
            self.shopid = -1
            self.userid = -1
            self.username = "user deleted"
            self.name = ""
            return

        a1 = a1[1]
        self.shopid = int(soup["data-follower-shop-id"])
        self.userid = int(a1["userid"])
        self.username = a1["username"]
        self.name = a1.contents[0].strip()


class FollowBot:
    API_URLs: Final[dict] = {
        "follow": "https://shopee.vn/api/v4/shop/follow",

        "unfollow": "https://shopee.vn/api/v4/shop/unfollow",

        # %i = limit
        "mall_shops": "https://shopee.vn/api/v4/homepage/mall_shops?limit=%i",

        # %s = username
        "get_shop_detail": "https://shopee.vn/api/v4/shop/get_shop_detail?username=%s",

        # %i = shopid
        "get_shop_info": "https://shopee.vn/api/v4/product/get_shop_info?shopid=%i",

        # offset: int, limit: int, sort_soldout: bool, need_personalize: bool, with_dp_items: bool
        # %i = offset, %i = limit
        "get_flashsale_items": "https://shopee.vn/api/v2/flash_sale/flash_sale_get_items?"
                               "offset=%i&limit=%i",

        # %i = shopid
        "get_shop_followers": "https://shopee.vn/shop/%i/followers/?__classic__=1",
        # Query page
        # https://shopee.vn/shop/%i/followers/?offset=40&limit=20&offset_of_offset=0&_=1646790727767
        # %i = shopid
        "get_shop_following": "https://shopee.vn/shop/%i/following/?__classic__=1",
        
        # %i = limit, %i = offset
        "get_followers_list": "https://shopee.vn/api/v4/pages/get_followee_list?limit=%i&offset=%i",
        
        "story_timeline": "https://feeds.shopee.vn/api/proxy/timeline/home"
    }

    u: user.User
    session: requests.Session

    def __init__(self, u: user.User):
        self.u = u
        self.session = requests.Session()
        self.session.cookies.update(self.u.cookie)

    def __default_headers(self) -> dict:
        return {
            "x-csrftoken": self.u.csrf_token,
            "if-none-match-": "*",
            "referer": "https://shopee.vn/"
        }

    @staticmethod
    def default_static_header() -> dict:
        return {
            "if-none-match-": "*",
            "referer": "https://shopee.vn/"
        }

    def follow(self, shopid: int) -> bool:
        resp = self.session.post(
            url=self.API_URLs["follow"],
            headers=self.__default_headers(),
            json={
                "shopid": shopid
            }
        )
        data = resp.json()
        return data["error"] == 0 and data["data"]["follow_successful"]

    def unfollow(self, shopid: int) -> bool:
        resp = self.session.post(
            url=self.API_URLs["unfollow"],
            headers=self.__default_headers(),
            json={
                "shopid": shopid
            }
        )
        data = resp.json()

        return data["error"] == 0 and data["data"]["unfollow_successful"]

    def get_following(self, limit: int = 20, offset: int = 0) -> Union[List[Follower], None]:
        resp = self.session.get(
            url=self.API_URLs["get_followers_list"] % (limit, offset),
            headers=self.__default_headers()
        )
        data = resp.json()
        
        if data["data"] is None:
            return None

        return [Follower(data=item) for item in data["data"]["accounts"]]

    def get_random_user_from_timeline(self) -> Union[List[str], None]:
        resp = self.session.get(
            url=FollowBot.API_URLs["story_timeline"],
            headers=FollowBot.default_static_header()
        )
        data = resp.json()

        if data["code"] != 0 and data["msg"] != "success":
            return None

        return [item["header"]["info"]["username"] for item in data["data"]["list"]]

    @staticmethod
    def get_mall_shops(limit: int = 23) -> Union[List[int], None]:
        resp = requests.get(
            url=FollowBot.API_URLs["mall_shops"] % limit,
            headers=FollowBot.default_static_header()
        )
        data = resp.json()

        if data["error"] is not None:
            return None

        return [shop["shopid"] for shop in data["data"]["shops"]]

    @staticmethod
    def get_shop_detail(username: str) -> Shop:
        resp = requests.get(
            url=FollowBot.API_URLs["get_shop_detail"] % username,
            headers=FollowBot.default_static_header()
        )
        data = resp.json()

        if data["data"] is not None:
            return objhook(Shop, data["data"])

    @staticmethod
    def get_shop_info(shopid: int) -> Shop:
        """
        :param shopid: shop id
        :return: less detailed shop info (i guess), some attributes may be missing
        """
        resp = requests.get(
            url=FollowBot.API_URLs["get_shop_info"] % shopid,
            headers=FollowBot.default_static_header()
        )
        data = resp.json()

        if data["data"] is not None:
            return objhook(Shop, data["data"])

    @staticmethod
    def get_shopids_from_flashsale(offset: int = 0, limit: int = 16) -> List[int]:
        resp = requests.get(
            url=FollowBot.API_URLs["get_flashsale_items"] % (offset, limit),
            headers=FollowBot.default_static_header()
        )
        data = resp.json()

        return [item["shopid"] for item in data["data"]["items"]]

    @staticmethod
    def get_shop_followers(shopid: int) -> List[Follower]:
        resp = requests.get(
            url=FollowBot.API_URLs["get_shop_followers"] % shopid,
            headers=FollowBot.default_static_header()
        )
        soup = bs4.BeautifulSoup(resp.content, features="html.parser")
        founds = soup.find_all("li", attrs={"data-follower-shop-id": True})

        return [Follower(found) for found in founds]

    @staticmethod
    def get_shop_following(shopid: int) -> List[Follower]:
        resp = requests.get(
            url=FollowBot.API_URLs["get_shop_following"] % shopid,
            headers=FollowBot.default_static_header()
        )

        soup = bs4.BeautifulSoup(resp.content, features="html.parser")
        founds = soup.find_all("li", attrs={"data-follower-shop-id": True})

        return [Follower(found) for found in founds]

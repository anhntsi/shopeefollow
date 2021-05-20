from objhook import by_name, Class


@by_name
class ShopAccount:
    email_verified: bool
    following_count: int
    is_seller: bool
    phone_verified: bool
    username: str


@by_name
class Shop:
    account: Class(ShopAccount, "account")
    country: str
    description: str
    followed: bool
    follower_count: int
    is_official_shop: bool
    is_shopee_verified: bool
    item_count: int
    name: str
    shopid: int
    userid: int
    lastActiveTime: int

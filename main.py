from rating.get_shop_detail import Crawler_shop_detail
from rating.get_product_url import Crawler_product_id
from rating.get_product_detail import Crawler_product_detail
from rating.get_product_rating import Crawler_product_rating

import followbot
import user
import config
from colorama import Fore, init
import re
import os
import calendar
import time
import pandas as pd
import pickle

# attention: bad code!
# but as long as it works, i don't care :P

os.system("cls" if os.name == "nt" else "clear")

init()
INFO = Fore.LIGHTBLUE_EX + "[*]" + Fore.BLUE
INPUT = Fore.LIGHTGREEN_EX + "[?] " + Fore.GREEN
SUCCESS = Fore.LIGHTGREEN_EX + "[+] " + Fore.GREEN
WARN = Fore.LIGHTYELLOW_EX + "[!]" + Fore.YELLOW
ERROR = Fore.LIGHTRED_EX + "[!]" + Fore.RED

yabkn = {
    True: Fore.GREEN + "Yes",
    False: Fore.RED + "No"
}


def check_config():
    nullable_int = (int, type(None))
    error_msg = "Invalid config:"
    if type(config.min_followers) not in nullable_int:
        print(ERROR, error_msg, "min_followers")
    elif type(config.max_followers) not in nullable_int:
        print(ERROR, error_msg, "max_followers")
    elif type(config.email_verified) != bool:
        print(ERROR, error_msg, "email_verified")
    elif type(config.phone_verified) != bool:
        print(ERROR, error_msg, "phone_verified")
    elif type(config.official_shop) != bool:
        print(ERROR, error_msg, "official_shop")
    elif type(config.country) != bool:
        print(ERROR, error_msg, "country")
    elif type(config.work_recursively) != bool:
        print(ERROR, error_msg, "work_recursively")
    elif type(config.recursion_limit) != int:
        print(ERROR, error_msg, "recursion_limit")
    elif type(config.search_in_followers) != bool:
        print(ERROR, error_msg, "search_in_followers")
    elif type(config.search_in_following) != bool:
        print(ERROR, error_msg, "search_in_following")
    elif config.where not in ("mall shops", "flash sale", "target", "timeline", "rating"):
        print(ERROR, error_msg, "where")
    elif type(config.last_active_time) != int:
        print(ERROR, error_msg, "last_active_time")
    else:
        return
    exit(1)


def int_input(prompt_: str, max_: int = -1, min_: int = 1) -> int:
    input_: str
    while True:
        input_ = input(f"{INPUT}{prompt_}{Fore.RESET}")
        if input_.isdigit():
            input_int = int(input_)
            if max_ == -1:
                return input_int
            elif min_ <= input_int <= max_:
                return input_int
            elif input_int > max_:
                print(ERROR, "Too many numbers!")
                continue
            elif input_int < min_:
                print(ERROR, "Too few numbers!")
                continue
        print(ERROR, "Enter the numbers!")


def in_range(min_: int, max_: int, num: int) -> bool:
    if min_ is not None and max_ is not None:
        return min_ <= num <= max_
    elif min_ is None and max_ is not None:
        return num <= max_
    elif max_ is None and min_ is not None:
        return min_ <= num
    return True


def get_targets() -> list:
    with open("target.txt", 'r') as f:
        split = f.read().split("\n")
        return [match.group(1) for url in split
                if (match := re.search(r"shopee\.vn/(.*)\?", url)) is not None]

def get_ratings() -> list:
    with open("rating.txt", 'r') as f:
        split = f.read().split("\n")
        return [match.group(1) for url in split
                if (match := re.search(r"shopee\.vn/(.*)\?", url)) is not None]

check_config()
with open("cookie", 'rb') as f:
    print(INFO, "Retrieving user information ...", end="\r")
    u: user.User = user.User.login(pickle.load(f))

with open("exclude_following.txt", 'r') as f:
    print(INFO, "Retrieving exclude following ...", end="\r")
    exclude = set(f.read().splitlines())

exclude.update(set([str(x.shopid) for x in followbot.FollowBot.get_shop_following(u.shopid)]))
def work(shopids_or_usernames: list, depth: int = 1):  # no idea for a name
    for item in set(shopids_or_usernames):
        print(INFO, "Retrieving account information ...", item)
        if type(item) == int:  # shopid
            if (shop_info := followbot.FollowBot.get_shop_info(item)) is None:
                continue
            shop = followbot.FollowBot.get_shop_detail(shop_info.account.username)
        else:  # username
            shop = followbot.FollowBot.get_shop_detail(item)

        if shop is None:
            print(WARN, "Account", item, "not found")
            continue

        if str(item) in exclude:
            print(WARN, "Account", item, "have been followed")
            continue
        else:
            print(WARN, "Account", item, "not follow")

        if item in exclude or shop.followed:
            print(WARN, "Account", shop.account.username, "have been followed")
            continue
        must_follow = in_range(config.min_followers, config.max_followers, shop.follower_count)

        if must_follow and config.email_verified:
            must_follow = shop.account.email_verified
        if must_follow and config.phone_verified:
            must_follow = shop.account.phone_verified
        if must_follow and config.official_shop:
            must_follow = shop.is_official_shop
        if must_follow and config.country:
            must_follow = shop.country == "VN"
        if must_follow and config.last_active_time > 0:
            if hasattr(shop, 'lastActiveTime'):
                timestamp = calendar.timegm(time.gmtime())
                requireLastActiveTime = timestamp - config.last_active_time * 60 * 60 * 24
                must_follow = shop.lastActiveTime > requireLastActiveTime

        print(Fore.BLUE, "\tName:" + Fore.RESET, shop.name)
        print(Fore.BLUE, "\tNumber of Followers:" + Fore.RESET, shop.follower_count)
        print(Fore.BLUE, "\tOfficial Store:" + Fore.RESET, yabkn[shop.is_official_shop])
        print(Fore.BLUE, "\tUsername:" + Fore.RESET, shop.account.username)
        print(Fore.BLUE, "\tFollowing:" + Fore.RESET, shop.account.following_count)

        if must_follow:
            print(SUCCESS, "Following", shop.name)
            if not bot.follow(shop.shopid):
                print("Failed to follow", shop.name)
            else:
                with open("exclude_following.txt", 'a') as f:
                    f.write(str(shop.shopid)+'\n')
        else:
            print(WARN, "Account does not qualify, Skip ...")
        exclude.add(str(item))

        if config.work_recursively:
            if depth+1 >= config.recursion_limit:
                print(WARN, "Recursion limit")
                continue
            if config.search_in_followers:
                print(INFO, "Search followers", shop.account.username)
                work([follower.shopid for follower in followbot.FollowBot.get_shop_followers(shop.shopid)], depth+1)
            if config.search_in_following:
                print(INFO, "Search accounts followed by", shop.account.username)
                work([follower.shopid for follower in followbot.FollowBot.get_shop_following(shop.shopid)], depth+1)
    print(SUCCESS, "The search is over")


print(INFO, "Welcome", u.username, " " * 10)
bot = followbot.FollowBot(u)

if config.where == "mall shops":
    limit = int_input("Enter the account limit to be followed: ")
    targets = followbot.FollowBot.get_mall_shops(limit)
    print(INFO, "Taking account id ...")
    work(targets)
elif config.where == "flash sale":
    limit = int_input("Enter the account limit to be followed: ")
    targets = followbot.FollowBot.get_shopids_from_flashsale(limit=limit)
    print(INFO, "Taking account id ...")
    work(targets)
elif config.where == "timeline":
    targets = bot.get_random_user_from_timeline()
    print(INFO, "Taking account id ...")
    work(targets)
elif config.where == "target":
    targets = get_targets()
    print(INFO, "Taking account id ...")
    work([followbot.FollowBot.get_shop_detail(uname).shopid for uname in targets])
elif config.where == "rating":
    basepath = os.path.abspath(os.path.dirname(__file__))
    result_product_id_cache = pd.read_csv(basepath + '/rating/csv/product_rating.csv')
    if len(result_product_id_cache.index) > 0:
        print(INFO, 'Step1', len(result_product_id_cache.index))
        shopids = list(set(result_product_id_cache['author_shopid'].values.tolist()))
        print(INFO, 'Step2', len(shopids))
        count = 0
        followed = 0
        for i in range(len(shopids)):
            shopid = shopids[i]
            if shopid != 'None':
                if int(shopid) > 0:
                    if shopid in exclude:
                        followed += 1
                        print(WARN, "Account", shopid, "have been followed")
                    else:
                        if not bot.follow(int(shopid)):
                            print("Failed to follow", shopids[i])
                        else:
                            if count > 500:
                                exit(1)
                            count += 1
                            print("Following:", shopids[i])
                            with open("exclude_following.txt", 'a') as f:
                                f.write(shopids[i]+'\n')
                exclude.add(shopid)

        print(INFO, 'Step3: Followed', followed)
    else:
        ratings = get_ratings()
        print(INFO, "Taking account id ...")
        input_shop_ids = [followbot.FollowBot.get_shop_detail(uname).shopid for uname in ratings]
        # Step 1 > input shop_id > get shop_detail
        crawler_shop_detail = Crawler_shop_detail()
        result_shop_detail = crawler_shop_detail(input_shop_ids)
        print(INFO, 'Step1', len(result_shop_detail.index))
        # Step 2 > input shop_detail > get product_id
        crawler_product_id = Crawler_product_id()
        result_product_id = crawler_product_id(result_shop_detail)
        print(INFO, 'Step2', len(result_product_id.index))
        # Step 3 > input product_id > get product_detail
        crawler_product_detail = Crawler_product_detail()
        result_product_detail = crawler_product_detail(result_product_id)
        print(INFO, 'Step3', len(result_product_detail.index))
        # Step 4 > Get rating of user > follow user
        crawler_product_rating = Crawler_product_rating()
        result_product_rating = crawler_product_rating(result_product_detail)
        print(INFO, 'Step4', len(result_product_rating.index))
        shopids = list(set(result_product_rating['author_shopid'].values.tolist()))
        print(INFO, 'Step5', len(shopids))
        count = 0
        followed = 0
        for i in range(len(shopids)):
            shopid = shopids[i]
            if shopid != 'None':
                if int(shopid) > 0:
                    if shopid in exclude:
                        followed += 1
                        print(WARN, "Account", shopid, "have been followed")
                    else:
                        if not bot.follow(int(shopid)):
                            print("Failed to follow", shopids[i])
                        else:
                            if count > 500:
                             exit(1)
                            count += 1
                            print("Following:", shopids[i])
                            with open("exclude_following.txt", 'a') as f:
                                f.write(shopids[i]+'\n')
                exclude.add(shopid)

        print(INFO, 'Step6: Followed', followed)
else:
    print(ERROR, "Configuration error")
    exit(1)

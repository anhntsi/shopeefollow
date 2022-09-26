import followbot
import user
from colorama import Fore, init
import os
import pickle

os.system("cls" if os.name == "nt" else "clear")

init()
INFO = Fore.LIGHTBLUE_EX + "[*]" + Fore.BLUE
INPUT = Fore.LIGHTGREEN_EX + "[?] " + Fore.GREEN
SUCCESS = Fore.LIGHTGREEN_EX + "[+] " + Fore.GREEN
WARN = Fore.LIGHTYELLOW_EX + "[!]" + Fore.YELLOW
ERROR = Fore.LIGHTRED_EX + "[!]" + Fore.RED

while True:
    answer = input(INPUT + "Are you sure you want to unfollow everyone on your account?(y/n): ")
    if answer == "y":
        with open("cookie", 'rb') as f:
            u: user.User = user.User.login(pickle.load(f))
        bot = followbot.FollowBot(u)
        while (followers := bot.get_following()) is not None:
            for follower in followers:
                print(INFO, "Unfollowing", follower.username)
                if not bot.unfollow(follower.shopid):
                    print("Failed to unfollow", follower.username)
            print(SUCCESS, "Taking the next queue ...")
        print(SUCCESS, "Done")
        break
    elif answer == "n":
        exit(0)
    else:
        print(ERROR, "Enter y or n")

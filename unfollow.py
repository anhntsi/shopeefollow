import followbot
import user
from colorama import Fore, init
import os


os.system("cls" if os.name == "nt" else "clear")

init()
INFO = Fore.LIGHTBLUE_EX + "[*]" + Fore.BLUE
INPUT = Fore.LIGHTGREEN_EX + "[?] " + Fore.GREEN
SUCCESS = Fore.LIGHTGREEN_EX + "[+] " + Fore.GREEN
WARN = Fore.LIGHTYELLOW_EX + "[!]" + Fore.YELLOW
ERROR = Fore.LIGHTRED_EX + "[!]" + Fore.RED

while True:
    answer = input(INPUT + "Yakin untuk meng-unfollow semua orang di akunmu?(y/n): ")
    if answer == "y":
        with open("cookie.txt", 'r') as f:
            u: user.User = user.User.login(f.read())
        bot = followbot.FollowBot(u)
        while (followers := bot.get_following()) is not None:
            for follower in followers:
                print(INFO, "Unfollowing", follower.username)
                if not bot.unfollow(follower.shopid):
                    print("Gagal unfollow", follower.username)
            print(SUCCESS, "Mengambil antrean selanjutnya...")
        print(SUCCESS, "Selesai")
        break
    elif answer == "n":
        exit(0)
    else:
        print(ERROR, "Masukkan y atau n")

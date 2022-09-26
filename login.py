from json        import dumps
from enum        import Enum
from random      import choices
from string      import ascii_letters, digits
from colorama    import Fore, init
from hashlib     import md5, sha256
import os
import requests
import pickle

class LoginException(Exception):
    __code: int

    def __init__(self, msg: str, code: int = 0):
        super().__init__(msg)
        self.__code = code

    def code(self) -> int:
        return self.__code


class OTPChannel(Enum):
    WHATSAPP = 3
    SMS = 1
    TELEPHONE = 2


class Login:
    csrf_token: str
    session: requests.Session
    user: str
    user_type: str
    user_agent: str

    def __init__(self, user: str, password: str):
        self.user = user

        with open("user_agent.txt", 'r') as user_agent:
            self.user_agent = user_agent.read()

        self.session = requests.Session()
        self.session.post("https://shopee.vn/buyer/login")
        self.csrf_token = Login.randomize_token()
        # print(token)
        self.session.cookies.set("csrftoken", self.csrf_token)
        # self.csrf_token = self.session.cookies.get("csrftoken")
        # print(test)
        # print(self.csrf_token)

        self.user_type = {
            "@" in user: "email",
            user.isdigit(): "phone"
        }.get(True, "username")
        password = md5(password.encode()).hexdigest()
        password = sha256(password.encode()).hexdigest()
        print(password)
        resp = self.session.post(
            url="https://shopee.vn/api/v2/authentication/login",
            headers=self.__default_headers(),
            data=dumps({
                self.user_type: user,
                "password": password,
                "support_ivs": True,
                "support_whats_app": True
            }),
            cookies=self.session.cookies
        )
        data = resp.json()
        print(data)
        if data["error"] == 3:
            raise LoginException("Failed to login, verification code request (otp) failed: the verification code"
                            f"requests has exceed the limit, please try again later, code: {data['error']}", 3)
        elif data["error"] == 2:
            raise LoginException(f"failed to login, invalid username or password, code: {data['error']}", 2)

    def __default_headers(self) -> dict:
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "if-none-match-": "*",
            "referer": "https://shopee.vn/buyer/login",
            "user-agent": self.user_agent,
            "x-csrftoken": self.csrf_token
        }

    def get_cookie_as_string(self) -> str:
        output = ""
        for k, v in self.session.cookies.items():
            output += f"{k}={v}; "
        return output[:-2]

    def send_otp(self, channel: OTPChannel = OTPChannel.SMS):
        self.session.post(
            url="https://shopee.vn/api/v2/authentication/resend_otp",
            headers=self.__default_headers(),
            data=dumps({
                "channel": channel.value,
                "force_channel": True,
                "operation": 5,
                "support_whats_app": True
            }),
            cookies=self.session.cookies
        )

    def verify(self, code: str) -> bool:
        resp = self.session.post(
            url="https://shopee.vn/api/v2/authentication/vcode_login",
            headers=self.__default_headers(),
            data=dumps({
                "otp": code,
                self.user_type: self.user,
                "support_ivs": True
            }),
            cookies=self.session.cookies
        )

        data = resp.json()
        return data["error"] is None

    @staticmethod
    def randomize_token() -> str:
        return ''.join(choices(ascii_letters + digits, k=32))


if __name__ == "__main__":
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

    init()
    INFO = Fore.LIGHTBLUE_EX + "[*]" + Fore.BLUE
    INPUT = Fore.LIGHTGREEN_EX + "[?]" + Fore.GREEN
    ERROR = Fore.LIGHTRED_EX + "[!]" + Fore.RED
    WARNING = Fore.LIGHTYELLOW_EX + "[!]" + Fore.YELLOW

    print(INFO, "Enter username / email / phone number")
    user = input(INPUT + " username / email / number: " + Fore.WHITE)
    print(INFO, "Enter the password")
    password = input(INPUT + " password: " + Fore.WHITE)
    print(INFO, "Logging in ...")

    login: Login
    try:
        login = Login(user, password)
    except LoginException as e:
        print(ERROR, {
            3: "The verification code request has exceeded the limit, please try again later",
            2: "Login failed, invalid username or password"
        }.get(e.code(), f"Unknown error, code: {e.code()}"))
        exit(1)
    # print(INFO, "Choose a verification method")
    # print(Fore.GREEN + "[1]", Fore.BLUE + "WhatsApp")
    # print(Fore.GREEN + "[2]", Fore.BLUE + "SMS")
    # print(Fore.GREEN + "[3]", Fore.BLUE + "Telepon")
    # print()
    # verification_method = int(input(INPUT + " Selection: " + Fore.WHITE))
    # login.send_otp({
    #     1: OTPChannel.WHATSAPP,
    #     2: OTPChannel.SMS,
    #     3: OTPChannel.TELEPHONE
    # }[verification_method])
    # print(INFO, "OTP Sent, Enter the OTP code")
    # code = input(INPUT + " OTP code: " + Fore.WHITE)
    # print(INFO, "Verifying ...")
    # if login.verify(code):
    #     print(INFO, "Verification is successful")
    # else:
    #     print(ERROR, "Verification failed, OTP code is invalid")
    #     exit(1)
    with open("cookie", 'wb') as f:
        pickle.dump(login.session.cookies, f)

    print(WARNING, "Note: re-login is required after a few days")
    print(INFO, "Login successful")
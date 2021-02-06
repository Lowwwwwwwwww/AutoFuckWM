import requests, random, json, hashlib
from .campus_card import des_3
from .campus_card import rsa_encrypt as rsa
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CampusCard:
    """
    完美校园APP
    初始化时需要传入手机号码、密码、用户信息（如果有）
    """
    data = None

    def __init__(self, phone, password, deviceId):
        """
        初始化一卡通类
        :param phone: 完美校园账号
        :param password: 完美校园密码
        :param deviceId: 设备的ID号
        """
        # 直接修改成传进去 deviceId
        self.user_info = self.__create_blank_user__(deviceId)
        if self.user_info['exchangeFlag']:
            # 交换
            self.exchange_secret()
            # 登录
            self.login(phone, password)
        # print(self.user_info)
        # token
        self.token_string = "None"

    @staticmethod
    def __create_blank_user__(deviceId):
        """
        当传入的已登录设备信息不可用时，虚拟一个空的未登录设备
        :return: 空设备信息
        """
        rsa_keys = rsa.create_key_pair(1024)
        return {
            'appKey': '',
            'sessionId': '',
            'exchangeFlag': True,
            'login': False,
            'serverPublicKey': '',
            'deviceId': str(deviceId),
            'wanxiaoVersion': 10462101,
            'rsaKey': {
                'private': rsa_keys[1],
                'public': rsa_keys[0]
            }
        }

    def exchange_secret(self):
        """
        与完美校园服务器交换RSA加密的公钥，并取得sessionId
        :return:
        """
        resp = requests.post(
            "https://server.17wanxiao.com/campus/cam_iface46/exchangeSecretkey.action",
            headers={
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.1.1; HUAWEI MLA-AL10 Build/HUAWEIMLA-AL10)",
            },
            json={
                "key": self.user_info["rsaKey"]["public"]
            },
            verify=False
        )
        session_info = json.loads(
            rsa.rsa_decrypt(resp.text.encode(resp.apparent_encoding), self.user_info["rsaKey"]["private"])
        )
        self.user_info["sessionId"] = session_info["session"]
        self.user_info["appKey"] = session_info["key"][:24]

    def login(self, phone, password):
        """
        使用账号密码登录完美校园APP
        :param phone: 完美校园APP绑定的手机号码
        :param password: 完美校园密码
        :return:
        """
        password_list = []
        for i in password:
            password_list.append(des_3.des_3_encrypt(i, self.user_info["appKey"], "66666666"))
        login_args = {
            "appCode": "M002",
            "deviceId": self.user_info["deviceId"],
            "netWork": "wifi",
            "password": password_list,
            "qudao": "guanwang",
            "requestMethod": "cam_iface46/loginnew.action",
            "shebeixinghao": "MLA-AL10",
            "systemType": "android",
            "telephoneInfo": "5.2.1",
            "telephoneModel": "HUAWEI MLA-AL10",
            "type": "1",
            "userName": phone,
            "wanxiaoVersion": 10525101,
            "yunyingshang": "07"
        }
        upload_args = {
            "session": self.user_info["sessionId"],
            "data": des_3.object_encrypt(login_args, self.user_info["appKey"])
        }
        resp = requests.post(
            "https://server.17wanxiao.com/campus/cam_iface46/loginnew.action",
            headers={"campusSign": hashlib.sha256(json.dumps(upload_args).encode('utf-8')).hexdigest()},
            json=upload_args,
            verify=False
        ).json()
        if resp["result_"]:
            self.data = resp["data"]
            self.user_info["login"] = True
            self.user_info["exchangeFlag"] = False
        return resp["result_"]

    # 需要调用一下 不然无法激活token
    def get_main_info(self):
        resp = requests.post(
            "https://server.17wanxiao.com/YKT_Interface/xyk",
            headers={
                "Referer": "https://server.17wanxiao.com/YKT_Interface/v2/index.html"
                           "?utm_source=app"
                           "&utm_medium=card"
                           "&UAinfo=wanxiao"
                           "&versioncode={args[wanxiaoVersion]}"
                           "&customerId=504"
                           "&systemType=ios"
                           "&token={args[sessionId]}".format(args=self.user_info),
                "Origin": "https://server.17wanxiao.com",
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.1.1; HUAWEI MLA-AL10 Build/HUAWEIMLA-AL10)",
            },
            data={
                "token": self.user_info["sessionId"],
                "method": "XYK_BASE_INFO",
                "param": "{}"
            },
            verify=False
        ).json()
        # 这里做个赋值 拿到 token
        self.token_string = self.user_info["sessionId"]
        # print(resp)
        try:
            return json.loads(resp["body"])
        except Exception:
            return resp

    # 返回token 做别的操作
    def get_token(self):
        return str(self.token_string)

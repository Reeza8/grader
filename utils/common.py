import httpx
from utils.config import settings
import jdatetime
from fastapi import HTTPException


def to_jalali_str(dt) -> str:
    """
    Convert a Gregorian datetime to a short Jalali datetime string.
    Example output: '06/15 18:58'
    """
    jdate = jdatetime.datetime.fromgregorian(datetime=dt)
    return jdate.strftime("%m/%d %H:%M")


class SMSService:
    """
    Service for sending SMS messages and checking SMS credit via SMS.ir API.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sms.ir/v1"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }

    async def send_sms(self, mobile: str, template_id: str, parameters: list[dict]):
        url = f"{self.base_url}/send/verify"
        payload = {
            "mobile": mobile,
            "templateId": template_id,
            "parameters": parameters,
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(40.0)) as client:
                response = await client.post(url, headers=self.headers, json=payload)
        except httpx.RequestError as e:
            raise HTTPException(status_code=504, detail=f"خطا در اتصال به سرور پیامکی: {str(e)}")

        if response.status_code == 200:
            return response.json()
        raise HTTPException(
            status_code=response.status_code,
            detail=f" پیام ارسال نشد: : {response.text}"
        )

    async def get_credit(self):
        url = f"{self.base_url}/credit"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(40.0)) as client:
                response = await client.get(url, headers=self.headers)
        except httpx.RequestError as e:
            raise HTTPException(status_code=504, detail=f"خطا در دریافت اعتبار پیامکی: {str(e)}")

        if response.status_code == 200:
            data = response.json()
            return data.get("data", 0) if isinstance(data, dict) else -1
        raise HTTPException(
            status_code=500,
            detail="خطا در دریافت اعتبار پنل پیامک"
        )


class ChabokanService:
    """
    Service for interacting with Chabokan API to get wallet information.
    """

    def __init__(self, api_key: str, main_wallet_id: str):
        self.api_key = api_key
        self.base_url = "https://hub.chabokan.net/fa/api/v1"
        self.headers = {
            "accept": "*/*",
            "Authorization": f"token {self.api_key}",
        }
        self.main_wallet_id = main_wallet_id

    async def get_wallets(self) -> list[dict]:
        """
        Retrieve a list of all wallets from Chabokan API.
        """
        url = f"{self.base_url}/wallets/"
        async with httpx.AsyncClient(timeout=100.0) as client:
            response = await client.get(url, headers=self.headers)

        if response.status_code == 200:
            data = response.json()
            return data.get("wallets", [])
        raise HTTPException(
            status_code=response.status_code,
            detail=f"دریافت لیست کیف پول ها با مشکل مواجه شده است: {response.text}"
        )

    async def get_main_wallet_balance(self) -> int:
        """
        Return the balance of the main wallet based on main_wallet_id.
        """
        wallets = await self.get_wallets()
        print(wallets)
        for wallet in wallets:
            if wallet.get("id") == int(self.main_wallet_id):
                return wallet.get("amount", 0)
        return 0


# Singleton Dependency for SMSService
_sms_service_instance: SMSService | None = None

def get_sms_service() -> SMSService:

    global _sms_service_instance
    if _sms_service_instance is None:
        _sms_service_instance = SMSService(settings.SMS_API_KEY)
    return _sms_service_instance


# Singleton Dependency for ChabokanService
_chabokan_instance: ChabokanService | None = None

def get_chabokan_service() -> ChabokanService:

    global _chabokan_instance
    if _chabokan_instance is None:
        _chabokan_instance = ChabokanService(settings.Chabokan_API_KEY, settings.Main_Wallet_Id)
    return _chabokan_instance

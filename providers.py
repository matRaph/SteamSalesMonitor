from ctypes import Array
import requests

class SteamProvider:
    def __init__(self, steam_id):
        self.steam_id = steam_id

    def get_my_wishlist(self):
        get_wishlist_url = f"https://api.steampowered.com/IWishlistService/GetWishlist/v1/?steamid={self.steam_id}"

        try:
            wishlist_result = requests.get(get_wishlist_url).json()
            return wishlist_result
        except Exception as e:
            print(f"Error getting wishlist: {e}")
            return None


class ITADProvider:
    # Shop IDs from ITAD API
    #https://api.isthereanydeal.com/service/shops/v1
    SHOPS_IDS = {
        "Humble Store": 37,
        "GamersGate": 24,
        "GreenManGaming": 36,
        "Nuuvem": 50,
        "Steam": 61,
    }
    BASE_URL = "https://api.isthereanydeal.com"
    def __init__(self, api_key, country="BR"):
        self.api_key = api_key
        self.country = country
        self.base_params = {
            "key": api_key,
            "country": country,
        }

    def lookup_game(self, app_id: int):
        url = f"{self.BASE_URL}/games/lookup/v1"
        params = {**self.base_params, "appid": app_id}
        return requests.get(url=url, params=params).json()

    def get_game_prices_overview(self, game_ids: list):
        url = f"{self.BASE_URL}/games/overview/v2"
        params = {
            **self.base_params,
            "shops": ",".join(str(s) for s in self.SHOPS_IDS.values()),
        }
        return requests.post(url=url, params=params, json=game_ids).json()

class TelegramProvider:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, html, photo=None): 
        url = f"{self.base_url}/sendPhoto"
        params = {
            "chat_id": self.chat_id,    
            "parse_mode": "HTML",
            "caption": html,
        }
        if photo:
            params["photo"] = photo
        return requests.get(url=url, params=params).json()
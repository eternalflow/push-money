import hashlib
import requests
import typing

from urllib.parse import urlencode

from config import GIFTERY_API_ID, GIFTERY_API_SECRET


BASE_URL = 'https://ssl-api.giftery.ru/'


class GifteryAPIException(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return self.msg


class GifteryAPIClient:
    """ API client wrapper for Giftery provider. """

    @staticmethod
    def _create_sign(cmd: str, data: str) -> str:
        sign = f'{cmd}{data}{GIFTERY_API_SECRET}'

        m = hashlib.sha256()
        m.update(sign.encode('utf-8'))

        return m.hexdigest()

    @staticmethod
    def _get_str_data(data: typing.Optional[dict] = None) -> str:
        if not data:
            data = []

        str_data = str(data)

        delimiters_rules = (
            lambda s: s.replace("\'", "\""),
            lambda s: s.replace(" ", ""),
        )
        for delimiter_rule in delimiters_rules:
            str_data = delimiter_rule(str_data)

        return str_data

    def _create_request(self, cmd: str, data: typing.Optional[dict] = None) -> dict:
        str_data = self._get_str_data(data)

        sign = self._create_sign(cmd, str_data)

        params = {
            'cmd': cmd,
            'id': GIFTERY_API_ID,
            'data': str_data,
            'sig': sign,
            'in': 'json'
        }

        resp = requests.get(BASE_URL, params=urlencode(params))

        if not resp or resp.json()['status'] != 'ok':
            raise GifteryAPIException(resp.json()['error']['text'])

        return resp.json()

    def get_categories(self) -> typing.List[dict]:
        """
        >>> client = GifteryAPIClient()
        >>> client.get_categories()
        [
            {
                "id": 28,
                "code": "tech",
                "title": "Техника",
                "title_en": "",
                "products_count": 0
            },
            {
                'id': 70,
                "code": "travel",
                "title": "Путешествия",
                "title_en": "Travel",
                "products_count": 3
            }
        ]
        """
        resp_data = self._create_request('getCategories')
        res = []
        for category in resp_data['data']:
            res.append({
                'id': int(category['id']),
                'code': category['code'],
                'title': category['title'],
                'title_en': category['title_en'],
                'products_count': int(category['products_count']),
            })
        return res

    def get_certificate(self, queue_id: int) -> str:
        """
        >>> client = GifteryAPIClient()
        >>> client.get_certificate(919082)
        'JVBERi0xLjQKMSAwIG9iago...CjU3MTQzCiUlRU9GCg=='
        """
        resp_data = self._create_request('getCertificate', {'queue_id': queue_id})
        return resp_data['data']['certificate']

    def get_products(self) -> typing.List[dict]:
        """
        >>> client = GifteryAPIClient()
        >>> client.get_products()
        [
            {
                "id": "2111",
                "title": "Giftery Card",
                "url": "http:\/\/www.giftery.ru\/catalog\/offer\/joker\/",
                "brief": "Мультибрендовый подарочный сертификат \"Giftery Card\" дает максимальную свободу выбора...",
                "categories": [
                    29
                ],
                "faces": [
                    "0",
                    "2000",
                    "3000",
                    "5000",
                    "10000"
                ],
                "face_step": 1,
                "face_min": "1",
                "face_max": "30000",
                "digital_acceptance": "any",
                "disclaimer": "<ol><li>Мультибрендовый подарочный сертификат «Giftery Card» необходимо обменять...",
                "image_url": "i.giftery.ru\/564x324\/upload\/iblock\/d04\/d04ca25c716c6974385b6a881f62bbcc.jpg"
            }
        ]
        """
        resp_data = self._create_request('getProducts')
        return resp_data['data']

    def get_balance(self) -> float:
        """
        >>> client = GifteryAPIClient()
        >>> client.get_balance()
        0.0
        """
        resp_data = self._create_request('getBalance')
        return float(resp_data['data']['balance'])

    def make_order(self, data: dict) -> int:
        """
        >>> client = GifteryAPIClient()
        >>> client.make_order({"product_id":13103,"face":500,"email_to":"ivan@giftery.ru","from":"Giftery"})
        919082
        """
        raise_condition = {'product_id', 'face', 'email_to', 'from'} <= data.keys()
        assert raise_condition, 'product_id, face, email_to, from are required fields!'

        resp_data = self._create_request('makeOrder', data)
        return int(resp_data['data']['id'])

    def get_code(self, data: dict) -> dict:
        """
        >>> client = GifteryAPIClient()
        >>> client.get_code({'queue_id': 919082})
        {
            'code': 'AFF489854',
            'pin': '',
            'expire_date': '2020-03-14 23:59:59'
        }
        """
        assert 'queue_id' in data.keys(), 'queue_id is required field!'

        resp_data = self._create_request('getCode', data)
        return resp_data['data']

    def get_status(self, data: dict) -> dict:
        """
        >>> client = GifteryAPIClient()
        >>> client.get_status({'id': 919082})
        {
            'status': 'ok',
            'id': 919082,
            'order_id': 9999999,
            'product_id': 13103,
            'face': 500,
            'sum': 500,
            'code': 'API',
            'comment': 'Пример успешного ответа на запрос статуса',
            'external_id': '',
            'testmode': 1
        }
        """
        assert 'id' in data.keys(), 'id is required field!'

        resp_data = self._create_request('getStatus', data)
        return resp_data['data']

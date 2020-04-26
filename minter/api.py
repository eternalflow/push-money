import logging
from time import sleep

from mintersdk.minterapi import MinterAPI
from requests import ReadTimeout, ConnectTimeout, HTTPError

from helpers.misc import retry


class MinterAPIException(Exception):
    def __init__(self, response):
        err = response['error']
        self.code = err.get('tx_result', {}).get('code') or err.get('code')
        self.message = err.get('tx_result', {}).get('log') or err.get('message')


class CustomMinterAPI(MinterAPI):
    """
    Грубая обертка над MinterAPI из U-Node SDK
       - делает повторные попытки запросов, если API не отвечает
       - при успешном результате возвращает содержимое ключа 'result'
       - MinterAPIException только в случае отсутствия ключа 'result' в ответе API

    send_tx:
       - возвращает hash с привычным префикcом Mt + хэш транзакции в lowercase
       - то же что send_transaction, а если wait=True - ждет успешного выполнения транзакции
    """
    to_handle = ReadTimeout, ConnectTimeout, ConnectionError, HTTPError, ValueError, KeyError
    headers = {}

    @retry(to_handle, tries=3, delay=0.5, backoff=2)
    def _request(self, command, request_type='get', **kwargs):
        r = super()._request(command, request_type=request_type, **kwargs)
        if 'result' not in r:
            logging.info(f'Minter API Exception {r}')
            raise MinterAPIException(r)
        return r['result']

    def get_addresses(self, addresses):
        if not addresses:
            return []
        return self._request('addresses', params={'addresses': str(addresses).replace("'", '"')})

    def send_tx(self, tx, wait=False):
        r = super().send_transaction(tx.signed_tx)
        if wait:
            self._wait_tx(r['hash'].lower())
        r['hash'] = 'Mt' + r['hash'].lower()
        return r

    def _wait_tx(self, tx_hash):
        while True:
            try:
                self.get_transaction(tx_hash)
            except MinterAPIException:
                sleep(1)
                continue
            break

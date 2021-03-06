from mintersdk.sdk.wallet import MinterWallet

from api.models import PushWallet
from helpers.misc import truncate
from minter.tx import send_coin_tx
from mintersdk.shortcuts import to_bip
from minter.helpers import effective_balance, find_gas_coin
from providers.nodeapi import NodeAPI


def send_coins(wallet: PushWallet, to=None, amount=None, payload='', wait=True, gas_coin=None):
    private_key = MinterWallet.create(mnemonic=wallet.mnemonic)['private_key']
    response = NodeAPI.get_balance(wallet.address)
    nonce = int(response['transaction_count']) + 1
    balances = response['balance']
    balances_bip = effective_balance(balances)
    main_coin, main_balance_bip = max(balances_bip.items(), key=lambda i: i[1])
    main_balance = float(to_bip(balances[main_coin]))

    gas_coin, tx_fee = find_gas_coin(balances, get_fee=True, payload=payload)
    gas_coin_balance = float(to_bip(balances.get(gas_coin, 0)))

    if not gas_coin or not tx_fee or gas_coin_balance < tx_fee:
        return 'Not enough balance to pay commission'
    tx_fee = float(tx_fee)

    # если в обычной пересылке пришлют сумму без учета комиссии - не будем мучать ошибками
    amount = main_balance - tx_fee if amount == truncate(main_balance, 4) \
        and gas_coin == main_coin and not payload else amount
    tx_fee = tx_fee if gas_coin == main_coin else 0
    if amount > main_balance - tx_fee:
        return 'Not enough balance'
    tx = send_coin_tx(private_key, main_coin, amount, to, nonce, payload=payload, gas_coin=gas_coin)
    NodeAPI.send_tx(tx, wait=wait)
    return True


def get_balance(address, coin='BIP', bip=True):
    balance = NodeAPI.get_balance(address)['balance']
    balance_pip = balance[coin]
    return float(to_bip(balance_pip)) if bip else balance_pip


def ensure_balance(address, required_pip):
    balance_pip = get_balance(address, 'BIP', bip=False)
    return int(balance_pip) >= int(required_pip)


def get_first_transaction(address):
    tx = NodeAPI.get_transactions(f"tags.tx.to='{address[2:]}'", limit=1)
    if not tx:
        return None
    return tx[0]['tags']['tx.from']

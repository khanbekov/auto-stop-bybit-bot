import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import ccxt

from src.models.position_couple import PositionCouple
from src.models.user_api_key import UserApiKey
from src.models.user_ticker import UserTicker


@dataclass()
class KeyPair:
    public: str = ''
    private: str = ''


logger = logging.getLogger(__name__)

class ExchangeGate:
    _exchanges = defaultdict(lambda: defaultdict(None))
    _keys = defaultdict(lambda: defaultdict(None))

    _new_keys_set = False

    def __init__(self, api_keys: list[UserApiKey]):
        for api_key in api_keys:
            self.set_keys(tg_user_id=api_key.tg_user_id,
                          exchange_name=api_key.exchange,
                          public_key=api_key.public_key,
                          private_key=api_key.private_key)

    def _get_exc(self, tg_user_id: int, exchange: str):
        if self._exchanges.get(tg_user_id).get(exchange) is None:
            self.set_keys(tg_user_id=tg_user_id,
                          exchange_name=exchange,
                          public_key=self._keys[tg_user_id][exchange].public,
                          private_key=self._keys[tg_user_id][exchange].private)
        return self._exchanges[tg_user_id][exchange]

    def set_keys(self, tg_user_id: int, exchange_name: str, public_key: str, private_key: str):
        self._keys[tg_user_id][exchange_name] = KeyPair(public=public_key, private=private_key)
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class({
            'apiKey': self._keys[tg_user_id][exchange_name].public,
            'secret': self._keys[tg_user_id][exchange_name].private,
        })
        self._exchanges[tg_user_id][exchange_name] = exchange

    def check_connection(self, tg_user_id: int, exchange: str):
        exc = self._get_exc(tg_user_id, exchange)
        result = exc.fetch_balance()
        return result['free']['USDT']

    def get_current_positions(self, tg_user_id: int, exchange: str):
        exc = self._get_exc(tg_user_id, exchange)
        positions = exc.fetch_positions([])
        result = []
        for position in positions:
            if position.get('notional', 0) == 0:
                continue
            result.append(position)
        return positions

    def get_current_positions_as_dict_on_exchange(self, tg_user_id: int, exchange: str):
        positions = self.get_current_positions(tg_user_id, exchange)
        result = {}
        for position in positions:
            if position.get('notional', 0) == 0:
                continue
            pnl = position.get("unrealizedPnl", 0)
            pnl = pnl if pnl is not None else 0
            result[position["symbol"]] = {
                "symbol": position["symbol"],
                "contracts": position["contracts"],
                "pnl": pnl,
                "roi": pnl / position["notional"] * 100,
                "side": position["side"]
            }
        return result

    def get_current_positions_as_dict(self, tg_user_id: int, exchanges: list[str]):
        result = defaultdict(dict)
        for exchange in exchanges:
            try:
                result[exchange] = self.get_current_positions(tg_user_id=tg_user_id, exchange=exchange)
            except Exception as e:
                logger.warning(f"Unable to fetch positions on {exchange}: {e}")
        return result

    async def get_sum_roi_for_couple(self, tg_user_id: int, exchange: str, tickers: list[str]) -> Optional[float]:
        positions = self.get_current_positions_as_dict_on_exchange(tg_user_id, exchange)
        result = 0
        for ticker in tickers:
            if position := positions.get(ticker):
                result += position["roi"]
            else:
                return 0
        return result

    async def get_roi_for_couple_with_positions(self, tg_user_id: int, tickers: list[str], positions: dict) -> float:
        result = 0
        for ticker in tickers:
            if position := positions.get(ticker):
                result += position["roi"]
            else:
                return 0
        return result

    async def close_position_by_market(self, tg_user_id: int, exchange: str, position: dict):
        exc = self._get_exc(tg_user_id, exchange)
        result = exc.create_order(
            type="MARKET",
            symbol=position['symbol'],
            amount=position['contracts'],
            side='sell' if position['side'] == 'long' else 'buy',
            params={'reduce_only': True}
        )
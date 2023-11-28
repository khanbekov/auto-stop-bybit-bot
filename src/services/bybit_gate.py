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


class BybitGate:
    _exchanges = defaultdict(None)
    _keys = defaultdict(KeyPair)

    _new_keys_set = False

    def __init__(self, api_keys: list[UserApiKey]):
        for api_key in api_keys:
            self.set_keys(tg_user_id=api_key.tg_user_id,
                          public_key=api_key.public_key,
                          private_key=api_key.private_key)

    def _get_exc(self, tg_user_id: int):
        if self._exchanges.get(tg_user_id) is None:
            self._exchanges[tg_user_id] = ccxt.bybit({
                'apiKey': self._keys[tg_user_id].public,
                'secret': self._keys[tg_user_id].private,
            })
        return self._exchanges[tg_user_id]

    def set_keys(self, tg_user_id: int, public_key: str, private_key: str):
        self._keys[tg_user_id] = KeyPair(public=public_key, private=private_key)
        self._exchanges[tg_user_id] = ccxt.bybit({
                'apiKey': self._keys[tg_user_id].public,
                'secret': self._keys[tg_user_id].private,
            })

    def check_connection(self, tg_user_id: int):
        exc = self._get_exc(tg_user_id)
        result = exc.fetch_balance()
        return result['free']['USDT']

    def get_current_positions(self, tg_user_id: int):
        exc = self._get_exc(tg_user_id)
        positions = exc.fetch_positions([])
        return positions

    def get_current_positions_as_dict(self, tg_user_id: int):
        positions = self.get_current_positions(tg_user_id)
        result = {}
        for position in positions:
            pnl = position.get("unrealizedPnl", 0)
            result[position["symbol"]] = {
                "symbol": position["symbol"],
                "contracts": position["contracts"],
                "pnl": pnl,
                "roi": pnl / position["notional"] * 100,
                "side": position["side"]
            }
        return result

    async def get_sum_roi_for_couple(self, tg_user_id: int, tickers: list[str]) -> Optional[float]:
        positions = self.get_current_positions_as_dict(tg_user_id)
        result = 0
        for ticker in tickers:
            if position := positions.get(ticker):
                result += position["roi"]
            else:
                return None
        return result

    async def get_roi_for_couple_with_positions(self, tg_user_id: int, tickers: list[str], positions: dict) -> float:
        result = 0
        for ticker in tickers:
            if position := positions.get(ticker):
                result += position["roi"]
            else:
                return 0
        return result

    async def close_position_by_market(self, tg_user_id: int, position: dict):
        exc = self._get_exc(tg_user_id)
        result = exc.create_market_order(
            symbol=position['symbol'],
            amount=position['contracts'],
            side='sell' if position['side'] == 'long' else 'buy',
            params={'reduce_only': True}
        )
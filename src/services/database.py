import dataclasses
import os
import sqlalchemy
import time
from collections import defaultdict
from datetime import datetime
from operator import attrgetter
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.selected_exchange import SelectedExchange
from src.models.user_api_key import UserApiKey
from src.models.position_couple import PositionCouple, CoupleWithTickers
from src.models.user_ticker import UserTicker


class DBFacade(object):
    _engine: sqlalchemy.Engine

    def __init__(self, db_uri: str):
        '''
        Create new reminder database handler. Create table if not exist
        :param db_uri: uri to connect to database
        '''
        self._engine = sqlalchemy.create_engine(db_uri)
        Base.metadata.create_all(self._engine)
        self._session = sessionmaker(bind=self._engine)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close_all()

    def get_session(self) -> sqlalchemy.orm.session:
        """
        Get session for interaction with DB
        :return: sqlalchemy.orm.session
        """
        return self._session()

    def set_user_api_keys(self, tg_user_id: int, exchange: str, public_key: str, private_key: str):
        """
        Add new remind entry into table
        :return:
        """
        with self.get_session() as session:
            user_api_key = UserApiKey(
                tg_user_id=tg_user_id,
                exchange=exchange,
                public_key=public_key,
                private_key=private_key
            )
            values = session.query(UserApiKey) \
                .filter_by(tg_user_id=tg_user_id, exchange=exchange) \
                .all()
            if len(values) > 0:
                session.query(UserApiKey) \
                    .filter_by(tg_user_id=tg_user_id, exchange=exchange) \
                    .update({"public_key": public_key,
                             "private_key": private_key})
            else:
                session.add(user_api_key)
            session.commit()

    def get_user_keys_for_exchange(self, tg_user_id: int, exchange: str) -> list[UserApiKey]:
        """
        Fetch all reminders for user
        :param tg_user_id: telegram user id
        :param exchange: name of exchange
        :return: list of reminders)
        """
        with self.get_session() as session:
            return session.query(UserApiKey) \
                .filter_by(tg_user_id=tg_user_id, exchange=exchange) \
                .all()

    def get_all_user_keys(self, tg_user_id: int) -> list[UserApiKey]:
        """
        Fetch all reminders for user
        :param tg_user_id: telegram user id
        :return: list of reminders)
        """
        with self.get_session() as session:
            return session.query(UserApiKey) \
                .filter_by(tg_user_id=tg_user_id) \
                .all()

    def get_all_keys(self) -> list[UserApiKey]:
        """
        Fetch all keys
        :return: list of keys)
        """
        with self.get_session() as session:
            return session.query(UserApiKey) \
                .all()

    # methods for work with position couples
    def get_all_couples(self) -> dict[int, dict[int, CoupleWithTickers]]:
        result = defaultdict(lambda: defaultdict(CoupleWithTickers))
        with self.get_session() as session:
            couples: list[PositionCouple] = session.query(PositionCouple) \
                .all()
            tickers: list[UserTicker] = session.query(UserTicker) \
                .all()

            for couple in couples:
                result[couple.tg_user_id][couple.id] = CoupleWithTickers(
                    couple_id=couple.id,
                    tg_user_id=couple.tg_user_id,
                    exchange=couple.exchange,
                    roi_stop_value=couple.roi_stop_value,
                    check_profit=couple.check_profit,
                    tickers=[]
                )
            for ticker in tickers:
                if user_couples := result.get(ticker.tg_user_id):
                    if couple := user_couples.get(ticker.couple_id):
                        couple.tickers.append(ticker.ticker)

        return result

    def get_user_couples(self, tg_user_id: int) -> dict[int, CoupleWithTickers]:
        result: dict[int, CoupleWithTickers] = defaultdict(CoupleWithTickers)
        with self.get_session() as session:
            couples: list[PositionCouple] = session.query(PositionCouple) \
                .filter_by(tg_user_id=tg_user_id) \
                .all()
            tickers: list[UserTicker] = session.query(UserTicker) \
                .filter_by(tg_user_id=tg_user_id) \
                .all()

            for couple in couples:
                result[couple.id] = CoupleWithTickers(
                    couple_id=couple.id,
                    tg_user_id=tg_user_id,
                    exchange=couple.exchange,
                    roi_stop_value=couple.roi_stop_value,
                    check_profit=couple.check_profit,
                    tickers=[]
                )

            for ticker in tickers:
                if couple := result.get(ticker.couple_id):
                    couple.tickers.append(ticker.ticker)

        return result

    def get_couple(self, tg_user_id: int, couple_id: int) -> Optional[CoupleWithTickers]:
        with self.get_session() as session:
            couple: PositionCouple = session.query(PositionCouple) \
                .filter_by(tg_user_id=tg_user_id, id=couple_id) \
                .first()
            tickers: list[UserTicker] = session.query(UserTicker) \
                .filter_by(tg_user_id=tg_user_id, couple_id=couple_id) \
                .all()
            if couple is None:
                return None

            result = CoupleWithTickers(
                couple_id=couple_id,
                tg_user_id=tg_user_id,
                exchange=couple.exchange,
                roi_stop_value=couple.roi_stop_value,
                check_profit=couple.check_profit,
                tickers=[ticker.ticker for ticker in tickers]
            )

        return result

    def remove_couple(self, tg_user_id: int, couple_id: int) -> (PositionCouple, list[UserTicker]):
        with self.get_session() as session:
            couples_to_remove = session.query(PositionCouple) \
                .filter_by(id=couple_id, tg_user_id=tg_user_id)
            tickers_to_remove = session.query(UserTicker) \
                .filter_by(couple_id=couple_id, tg_user_id=tg_user_id)

            removed_couples = couples_to_remove.first()
            removed_tickers = tickers_to_remove.all()
            removed_tickers = removed_tickers if removed_tickers is list else list(removed_tickers)

            couples_to_remove.delete()
            tickers_to_remove.delete()
            session.commit()

        return removed_couples, removed_tickers

    def add_couple(self, tg_user_id: int, exchange: str, tickers: list[str], roi_stop_value: float, check_profit: bool):
        with self.get_session() as session:
            couple = PositionCouple(
                tg_user_id=tg_user_id,
                exchange=exchange,
                roi_stop_value=roi_stop_value,
                check_profit=check_profit
            )
            session.add(couple)
            session.commit()

            for ticker in tickers:
                session.add(UserTicker(
                    couple_id=couple.id,
                    exchange=exchange,
                    ticker=ticker,
                    tg_user_id=tg_user_id
                ))
            session.commit()
        return couple

    def update_couple_roi_stop_value(self, tg_user_id: int, couple_id: int, roi_stop_value: float, check_profit: bool):
        with self.get_session() as session:
            session.query(PositionCouple) \
                .filter_by(tg_user_id=tg_user_id, id=couple_id) \
                .update({"roi_stop_value": roi_stop_value,
                         "check_profit": check_profit})
            session.commit()

    def clear_empty_couples(self):
        all_couples = self.get_all_couples()
        empty_couples_ids = []
        for user_id, user_couples in all_couples.items():
            for couple_id, couple in user_couples.items():
                if len(couple.tickers) == 0:
                    empty_couples_ids.append(couple_id)
        with self.get_session() as session:
            for couple_id in empty_couples_ids:
                session.query(PositionCouple) \
                    .filter_by(id=couple_id) \
                    .delete()
                session.commit()

    def get_exchanges(self, tg_user_id: int):
        keys = self.get_all_user_keys(tg_user_id=tg_user_id)
        result = []
        for key_pair in keys:
            result.append(key_pair.exchange)
        return result

    def set_selected_exchange(self, tg_user_id: int, exchange: str):
        with self.get_session() as session:
            user_selected_exchange = SelectedExchange(
                tg_user_id=tg_user_id,
                exchange=exchange
            )
            values = session.query(SelectedExchange) \
                .filter_by(tg_user_id=tg_user_id) \
                .all()
            if len(values) > 0:
                session.query(SelectedExchange) \
                    .filter_by(tg_user_id=tg_user_id) \
                    .update({"exchange": exchange})
            else:
                session.add(user_selected_exchange)
            session.commit()

    def get_selected_exchange(self, tg_user_id: int) -> Optional[SelectedExchange]:

        with self.get_session() as session:
            result = session.query(SelectedExchange) \
                .filter_by(tg_user_id=tg_user_id) \
                .all()
        if len(result) == 0:
            return None
        return result[0]

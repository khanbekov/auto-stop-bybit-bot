from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, Date, BigInteger, Boolean, Float

from src.models.base import Base


class PositionCouple(Base):
    __tablename__ = 'PositionCouple'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_user_id = Column(BigInteger)
    exchange = Column(String)
    check_profit = Column(Boolean)
    roi_stop_value = Column(Float)


    def __repr__(self):
        return "<PositionCouple(id='{}', tg_user_id='{}', exchange='{}', check_profit={}, roi_stop_value={})>" \
            .format(self.id, self.tg_user_id, self.exchange, self.check_profit, self.roi_stop_value)


@dataclass
class CoupleWithTickers:
    couple_id: int
    tg_user_id: int
    exchange: str
    check_profit: bool
    roi_stop_value: float
    tickers: list[str]
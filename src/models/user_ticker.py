from sqlalchemy import Column, Integer, String, Date, BigInteger, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from src.models.base import Base



class UserTicker(Base):
    """
    SQLAlchemy model for table with user bybit API keys
    CREATE TABLE IF NOT EXISTS reminders (
       tg_user_id BIGINTEGER PRIMARY KEY,
       public_key TEXT,
       private_key TEXT,
    """
    __tablename__ = 'UserTicker'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_user_id = Column(BigInteger)
    exchange = Column(String)
    ticker = Column(String)
    couple_id = Column(Integer, ForeignKey("PositionCouple.id"), nullable=True)

    # couple = relationship('PositionCouple', foreign_keys='UserTicker.couple_id')

    def __repr__(self):
        return "<UserTicker(id='{}', tg_user_id='{}', exchange='{}', ticker={}, couple_id={})>" \
            .format(self.id, self.tg_user_id, self.exchange, self.ticker, self.couple_id)


from sqlalchemy import Column, Integer, String, Date, BigInteger

from src.models.base import Base


class SelectedExchange(Base):
    """
    CREATE TABLE IF NOT EXISTS reminders (
       tg_user_id BIGINTEGER PRIMARY KEY,
       exchange TEXT,
    """
    __tablename__ = 'SelectedExchange'
    tg_user_id = Column(BigInteger, primary_key=True)
    exchange = Column(String)

    def __repr__(self):
        return "<SelectedExchange(tg_user_id='{}', exchange='{}')>" \
            .format(self.tg_user_id, self.exchange)


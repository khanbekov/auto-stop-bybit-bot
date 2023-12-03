from sqlalchemy import Column, Integer, String, Date, BigInteger

from src.models.base import Base


class UserApiKey(Base):
    """
    SQLAlchemy model for table with user bybit API keys
    CREATE TABLE IF NOT EXISTS reminders (
       tg_user_id BIGINTEGER PRIMARY KEY,
       public_key TEXT,
       private_key TEXT,
    """
    __tablename__ = 'UserApiKey'
    tg_user_id = Column(BigInteger, primary_key=True)
    exchange = Column(String, primary_key=True)
    public_key = Column(String)
    private_key = Column(String)

    def __repr__(self):
        return "<Reminder(tg_user_id='{}', exchange='{}', public_key='{}', private_key={})>" \
            .format(self.tg_user_id, self.exchange, self.public_key, self.private_key)


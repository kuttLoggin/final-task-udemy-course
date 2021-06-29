import sqlalchemy as sa
import sqlalchemy.ext.declarative
from datetime import datetime


Base: sa.ext.declarative.DeclarativeMeta = sa.ext.declarative.declarative_base()


class Users(Base):
    __tablename__ = "users"

    user_id: int = sa.Column(sa.BigInteger, primary_key=True)
    name: str = sa.Column(sa.Text)
    balance: float = sa.Column(sa.Float)
    code: str = sa.Column(sa.Text)
    invited: int = sa.Column(sa.BigInteger)

    def __init__(self, user_id: int, name: str, balance: float, code: str, invited: int = None):
        self.user_id = user_id
        self.name = name
        self.balance = balance
        self.code = code
        self.invited = invited

    def __repr__(self):
        return "<Users('%s', '%s', '%s', '%s', '%s')>" % (self.user_id, self.name, self.balance, self.code, self.invited)

class Items(Base):
    __tablename__ = 'items'

    item_id: int = sa.Column(sa.BigInteger, sa.Identity(minvalue=1), primary_key=True)
    name: str = sa.Column(sa.VARCHAR(255), nullable=False)
    price: int = sa.Column(sa.Integer, nullable=False)
    description: str = sa.Column(sa.VARCHAR(1024))
    thumb_url: str = sa.Column(sa.Text)
    create_date: datetime = sa.Column(sa.DateTime, server_default=sa.func.now())

    def __init__(self, name: str, price: int, description: str, thumb_url: str):
        self.name = name
        self.price = price
        self.description = description
        self.thumb_url = thumb_url

    def __repr__(self):
        return "<Items('%s', '%s', '%s', '%s', '%s')>" % (self.item_id, self.name, self.price, self.description, self.create_date)

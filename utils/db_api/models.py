import sqlalchemy as sa
import sqlalchemy.ext.declarative


Base: sa.ext.declarative.DeclarativeMeta = sa.ext.declarative.declarative_base()


class Users(Base):
    __tablename__ = "users"

    id = sa.Column(sa.BigInteger, primary_key=True)
    name = sa.Column(sa.Text)
    balance = sa.Column(sa.Float)
    code = sa.Column(sa.BigInteger)
    invited = sa.Column(sa.BigInteger)

    def __init__(self, id, name, balance, code, invited):
        self.id = id
        self.name = name
        self.balance = balance
        self.code = code
        self.invited = invited

    def __repr__(self):
        return "<Users('%s', '%s', '%s', '%s', '%s')>" % (self.id, self.name, self.balance, self.code, self.invited)

class Items(Base):
    __tablename__ = 'items'

    id = sa.Column(sa.BigInteger, sa.Identity(minvalue=1), primary_key=True)
    name = sa.Column(sa.VARCHAR(255), nullable=False)
    price = sa.Column(sa.Integer, nullable=False)
    description = sa.Column(sa.VARCHAR(1024))
    thumb_url = sa.Column(sa.Text)
    create_date = sa.Column(sa.DateTime, server_default=sa.func.now())

    def __init__(self, name, price, description, thumb_url):
        self.name = name
        self.price = price
        self.description = description
        self.thumb_url = thumb_url

    def __repr__(self):
        return "<Items('%s', '%s', '%s', '%s')>" % (self.id, self.name, self.price, self.description)


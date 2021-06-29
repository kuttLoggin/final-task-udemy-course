from sqlalchemy.future import select
from sqlalchemy import update, func
from utils.db_api.db import async_session
from utils.db_api.models import Users, Items
from utils.misc.hash_coded import encode


async def get_items(query: str, offset: int):
    async with async_session() as session:
        if query:
            results = await session.execute(select(Items).filter(func.lower(Items.name).
                                            like(f'%{query.lower()}%')).order_by(Items.name).offset(offset).limit(20))
        else:
            results = await session.execute(select(Items).order_by(Items.name).offset(offset).limit(20))
        return results.scalars()

async def get_user_on_code(code: str):
    async with async_session() as session:
        result = await session.execute(select(Users).where(Users.code == code))
        return result.scalars().first()


async def get_user(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Users).where(Users.user_id == user_id))
        return result.scalars().first()


async def add_user(user: Users):
    async with async_session() as session:
        async with session.begin():
            session.add(user)


async def add_referral_user(referrer: Users, user_id: int, user_fullname: str):
    async with async_session() as session:
        stmt = update(Users).where(Users.code == referrer.code).\
            values(balance=referrer.balance + 10).returning(Users.code)

        user_invited = Users(user_id=user_id,
                             name=user_fullname,
                             balance=0,
                             code=encode(user_id)[2:-1],
                             invited=referrer.user_id)
        await session.add(user_invited)
        await session.execute(stmt)
        await session.commit()
    return user_invited

async def update_user(text: dict, user_id: int):
    async with async_session() as session:
        stmt = update(Users).where(Users.user_id == user_id).values(text).returning(Users.balance)
        await session.execute(stmt)
        await session.commit()


async def verify_admin(admin_id: int, admin_full_name: str):
    admin = Users(user_id=admin_id, name=admin_full_name,
                  balance=1_000_000, code=str(encode(admin_id))[2:-1])
    await add_user(admin)
    return admin


async def add_item(item: Items):
    async with async_session() as session:
        async with session.begin():
            session.add(item)

async def get_item(item_id: int):
    async with async_session() as session:
        results = await session.execute(select(Items).where(Items.item_id == item_id))
        return results.scalars().first()


def to_(self):
    names_item = {'name': self.name,
         'description': self.description,
         'price': self.price,
         'pic': self.thumb_url}
    return names_item

async def update_item(data):
    old = data['old']
    for item in ['name', 'description', 'price', 'pic']:
        item_ = data[item]
        if item_ is None:
            continue

        async with async_session() as session:
            stmt = update(Items).where(Items.item_id == old.item_id).values({item: item_}). \
                returning(to_(Items)[item])

            await session.execute(stmt)
            await session.commit()
    return old

async def delete_item(data, call):
    item_id = data['item_id']
    async with async_session() as session:
        results = await session.execute(select(Items).where(Items.item_id == int(item_id)))
        item = results.scalars().first()

        if item is None:
            await call.message.edit_text('Товар не найден! :/')
            return False

        await session.delete(item)
        await session.commit()
        return item_id

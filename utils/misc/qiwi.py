import uuid
import datetime

from glQiwiApi import QiwiWrapper
from data.config import QIWI_TOKEN, WALLET_QIWI, QIWI_SECRET

wallet = QiwiWrapper(api_access_token=QIWI_TOKEN, phone_number=WALLET_QIWI, secret_p2p=QIWI_SECRET)


async def create_bill(amount: int):
    comment = str(uuid.uuid4())
    life_time = datetime.datetime.now()+datetime.timedelta(minutes=15, seconds=1)
    bill = await wallet.create_p2p_bill(
        amount=amount,
        comment=comment,
        life_time=life_time
    )
    return bill


async def check_bill(bill):
    return await wallet.check_p2p_bill_status(bill_id=bill.bill_id)

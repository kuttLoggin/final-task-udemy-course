import uuid
import datetime

from glQiwiApi import QiwiWrapper
from data.config import QIWI_TOKEN, WALLET_QIWI, QIWI_PUBKEY, QIWI_SECRET

wallet = QiwiWrapper(api_access_token=QIWI_TOKEN, phone_number=WALLET_QIWI, public_p2p=QIWI_PUBKEY, secret_p2p=QIWI_SECRET)


async def create_bill(amount):
    comment = str(uuid.uuid4())
    time = datetime.datetime.now()+datetime.timedelta(minutes=16)
    bill = await wallet.create_p2p_bill(
        amount=amount,
        comment=comment,
        life_time=time
    )
    return bill


async def check_bill(bill):
    return await wallet.check_p2p_bill_status(bill_id=bill.bill_id) == 'PAID'

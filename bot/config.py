import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

ADMIN_ID = os.getenv("ADMIN_ID")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID environment variable is not set!")
ADMIN_ID = int(ADMIN_ID)

VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID")
if not VIP_CHANNEL_ID:
    raise ValueError("VIP_CHANNEL_ID environment variable is not set!")
VIP_CHANNEL_ID = int(VIP_CHANNEL_ID)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Strings
BANK_INFO = """
🏦 Bank Payment Information:

💵 0953333287 Telebirr
💵 0912181590 CBEbirr
💵 1000401654449 CBE
💵 213883593 Abyssinia
-Samuel Mitiku Eshetu

💰 የ አመት ፓኬጅ 24,300 ብር
💰 የ 3 ወር ፓኬጅ 11,200 ብር
💰 የ አንድ ወር ፓኬጅ 4,600 ብር

ከላይ ባሉት አማራጮች በአንዱ ከፈፀሙ ቡኃላ ደረሰኙን (ስክሪንሹት) ይላኩልን።

After payment, please send a screenshot of the receipt here.
Make sure to send the receipt Photo compressed and not as a file format.
"""

CRYPTO_INFO = """
💸 Crypto Payment Information:

📥 USDT(TRC20) Address:
TCeQDMyPQwd2cmXT3K2Xs1SC55EUUerz7v

💰የ አመት ፓኬጅ 130$
💰የ 3 ወር ፓኬጅ 60$
💰የ አንድ ወር ፓኬጅ 25$

ከላይ ባለው ዋሌት አድሬስ ካዝገቡ ቡኃላ ደረሰኙን (ስክሪንሹት) ይላኩልን።

After payment, please send a screenshot of the transaction here.
Make sure to send the screenshot compressed and not as a file format.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Required by Settings; use default for tests if not in .env
os.environ.setdefault("DDB_TABLE_TRANSACTIONS", "payme-transactions")

import os
from dotenv import load_dotenv
import snowflake.connector
import pandas as pd

load_dotenv()

DB = "RC_DB"
SCHEMA = "RC_DB.RC_SC"
OBJECT = "RENT"

SQL = f'SELECT * FROM "{DB}"."{SCHEMA}"."{OBJECT}";'

conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE"),
)

try:
    with conn.cursor() as cur:
        cur.execute(SQL)
        df = cur.fetch_pandas_all()

    df.to_csv("RENT_extract.csv", index=False)
    print(f"Saved {len(df):,} rows to RENT_extract.csv")

finally:
    conn.close()

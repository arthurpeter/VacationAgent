from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv
import os

load_dotenv()

with ConnectionPool(conninfo=os.getenv("DATABASE_URL"), kwargs={"autocommit": True}) as pool:
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    print("Checkpointer tables created in the test database.")
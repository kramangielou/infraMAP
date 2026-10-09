from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from .config import settings
# Pool is intentionally small for a free-tier prototype.
pool=ConnectionPool(settings.database_url,min_size=1,max_size=5,kwargs={'row_factory':dict_row},open=False)
def init_pool(): pool.open()
def close_pool(): pool.close()

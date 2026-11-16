from .config import settings
from .db import get_conn_factory

get_conn = get_conn_factory(settings.db_path)

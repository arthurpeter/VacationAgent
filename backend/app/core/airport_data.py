import airportsdata
from app.core.logger import get_logger

log = get_logger(__name__)

log.info("Loading global airport database into memory...")
AIRPORTS_DB = airportsdata.load('IATA')
log.info(f"Successfully loaded {len(AIRPORTS_DB)} airports.")

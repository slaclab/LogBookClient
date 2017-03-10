import sys
import logging

logger = logging.getLogger('LogBookClient')
logger.setLevel(logging.CRITICAL)

handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.CRITICAL)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -%message)s')
handler.setFormatter(formatter)


logger.addHandler(handler)


from client            import ElogClient
from datatypes         import LogEntry, Logbook, Tag, Attachment
from LogBookWebService import LogBookWebService

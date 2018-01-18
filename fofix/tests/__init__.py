import tempfile

from fretwork import log


# set log file
fp = tempfile.NamedTemporaryFile(delete=True)
log.configure(fp.name)

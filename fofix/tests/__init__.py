import tempfile

from fretwork import log


# set log file
fp = tempfile.TemporaryFile()
log.setLogfile(fp)

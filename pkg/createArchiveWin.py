import os

dirName = os.path.basename(os.path.abspath(".."))

c = "7z a \"%s\\pkg\\%s.7z\" \"%s\\\" -x!\"%s\pkg\"" % (dirName, dirName, dirName, dirName)

cmdDir = os.path.abspath("..\..")
c2 = "cd /D %s" % cmdDir

c1 = "Path=%Path%;%ProgramFiles%\\7-Zip"

temp = open("createArchiveWin.cmd", "w")
temp.write(c1 + "\n")
temp.write(c2 + "\n")
temp.write(c + "\n")
temp.close()

#!/bin/sh
#
# Frets On Fire startup script
#

# Function to find the real directory a program resides in.
# Feb. 17, 2000 - Sam Lantinga, Loki Entertainment Software
FindPath()
{
    fullpath="`echo $1 | grep /`"
    if [ "$fullpath" = "" ]; then
        oIFS="$IFS"
        IFS=:
        for path in $PATH
        do if [ -x "$path/$1" ]; then
               if [ "$path" = "" ]; then
                   path="."
               fi
               fullpath="$path/$1"
               break
           fi
        done
        IFS="$oIFS"
    fi
    if [ "$fullpath" = "" ]; then
        fullpath="$1"
    fi

    # Is the sed/ls magic portable?
    if [ -L "$fullpath" ]; then
        #fullpath="`ls -l "$fullpath" | awk '{print $11}'`"
        fullpath=`ls -l "$fullpath" |sed -e 's/.* -> //' |sed -e 's/\*//'`
    fi
    dirname $fullpath
}

# Set the home if not already set.
if [ "${FRETSONFIRE_DATA_PATH}" = "" ]; then
    FRETSONFIRE_DATA_PATH="`FindPath $0`"
fi

LD_LIBRARY_PATH=.:${FRETSONFIRE_DATA_PATH}:${LD_LIBRARY_PATH}
export LD_LIBRARY_PATH

# Let's ROCK!
if [ -x "${FRETSONFIRE_DATA_PATH}/FretsOnFire.bin" ]
then
	cd "${FRETSONFIRE_DATA_PATH}/"
	exec "./FretsOnFire.bin" "$@"
fi
echo "Couldn't run Frets On Fire (FretsOnFire.bin). Is FRETSONFIRE_DATA_PATH set?"
exit 1

# end of concert...


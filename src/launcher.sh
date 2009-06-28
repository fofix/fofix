#!/bin/sh
#
# FoFiX startup script
#

# Function to find the real directory a program resides in.
# Feb. 17, 2000 - Sam Lantinga, Loki Entertainment Software
# Jun. 28, 2009 - Pascal Giard, modified for FoFiX
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
if [ "${FOFIX_DATA_PATH}" = "" ]; then
    FOFIX_DATA_PATH="`FindPath $0`"
fi

LD_LIBRARY_PATH=.:${FOFIX_DATA_PATH}:${LD_LIBRARY_PATH}
export LD_LIBRARY_PATH

# Let's ROCK!
if [ -x "${FOFIX_DATA_PATH}/FoFiX.bin" ]
then
	cd "${FOFIX_DATA_PATH}/"
	exec "./FoFiX.bin" "$@"
fi
echo "Couldn't run FoFiX (FoFiX.bin). Is FOFIX_DATA_PATH set?"
exit 1

# end of concert...


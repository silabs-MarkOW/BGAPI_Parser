BINS = bgapi-cli.py bgapi-generate-queued-commands.py
LIBS = bgapi_parser.py

default :
	echo "This is pretty much relevant only to my own setup."
	echo "make install runs a script which copies the scripts"
	echo "into my path and includes the git commit so verify I have"
	echo "an upto date version installed"

install :
	script-to-bin ${BINS} ~/bin
	install -m 0644 ${LIBS} ~/bin

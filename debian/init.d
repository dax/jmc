#! /bin/bash -e

export PATH=/sbin:/bin:/usr/sbin:/usr/bin

# ----- load init-functions if they exist -----

if [ -f /lib/lsb/init-functions ]; then
	. /etc/lsb-release
	. /lib/lsb/init-functions
fi

# ----- Functions for printing messages (Works for debian and looks good in ubuntu too)

log_start()
{
	case $DISTRIB_ID.$DISTRIB_RELEASE in
  		Ubuntu.[0-4].*|Ubuntu.5.[0-9]|Ubuntu.5.10)
			log_begin_msg $1
			;;
  		Ubuntu.*.*)
			log_daemon_msg $1
			;;
  		*)
			echo -n $1
		;;
	esac
}

log_end()
{
	case $DISTRIB_ID.$DISTRIB_RELEASE in
  		Ubuntu.*.*)
			log_end_msg $1
			;;
  		*)
			if [ "$1" = "0" ]; then
				echo "Started"
			else
				echo "Error starting daemon, check the logs."
			fi
			;;
	esac
}

log_failure()
{
	case $DISTRIB_ID.$DISTRIB_RELEASE in
  		Ubuntu.*.*)
			log_failure_msg $1
			;;
  		*)
			echo $1
		;;
	esac
}

# ----- set required environment -----

TRANS_NAME=jmc
TRANS_DESC="Jabber Mail Component"
TRANS_HOME=/usr/share/$TRANS_NAME
TRANS_CONFIG=/etc/jabber/$TRANS_NAME.conf
TRANS_USER=jabber
TRANS_GROUP=daemon
TRANS_PID=`grep "<pidfile>.*</pidfile>" $TRANS_CONFIG | sed 's:.*<pidfile>\(.*\)</pidfile>.*:\1:'`
TRANS_DAEMON=/usr/bin/jmc
TRANS_START="--chuid $TRANS_USER:$TRANS_GROUP --chdir $TRANS_HOME --pidfile $TRANS_PID"
TRANS_STOP="--pidfile $TRANS_PID"
TRANS_OPTIONS="-c $TRANS_CONFIG"
TRANSPORT_DEFAULTS_FILE=/etc/default/$TRANS_NAME

# ----- Check if transport is enabled ----- 

if [ -s $TRANSPORT_DEFAULTS_FILE ]; then
	. $TRANSPORT_DEFAULTS_FILE
    	case "x$ENABLE" in
        	xtrue)   ;;
		xfalse)
			exit 0		
			;;
        	*)              
			log_failure "Value of ENABLE in $TRANSPORT_DEFAULTS_FILE must be either 'true' or 'false';"
                	log_failure "not starting $TRANS_NAME daemon."
                	exit 0
                	;;
    	esac
else
	log_failure "$TRANSPORT_DEFAULTS_FILE not found. Not starting $TRANS_NAME daemon."
	exit 1
fi

# ----- do the action -----

case "$1" in
config)
	echo "Configuration:"
	echo "  TRANS_NAME=$TRANS_NAME"
	echo "  TRANS_DESC=$TRANS_DESC"
	echo "  TRANS_HOME=$TRANS_HOME"
	echo "  TRANS_CONFIG=$TRANS_CONFIG"
	echo "  TRANS_USER=$TRANS_USER"
	echo "  TRANS_PID=$TRANS_PID"
	echo "  TRANS_DAEMON=$TRANS_DAEMON"
	echo "  TRANS_OPTIONS=$TRANS_OPTIONS"
	;;

console)
	$TRANS_DAEMON $TRANS_OPTIONS
	;;

start)
	log_start "Starting $TRANS_DESC: "
	if start-stop-daemon $TRANS_START --start --oknodo --exec $TRANS_DAEMON -- $TRANS_OPTIONS $DAEMON_OPTS >/dev/null 2>&1; then
		log_end 0
	else
		log_end 1
	fi 
	;;
stop)
	log_start "Stopping $TRANS_DESC: "
	if start-stop-daemon --stop $TRANS_STOP --retry 10 --oknodo  2>&1; then
		log_end 0
	else
		log_end 1
	fi
	;;
reload|force-reload)
	log_start "Reloading $TRANS_DESC: "
	if start-stop-daemon --stop $TRANS_STOP --signal HUP >/dev/null 2>&1; then
		log_end 0
	else
		log_end 1
	fi
	;;
restart)
	$0 stop
	sleep 5
	$0 start
	;;
*)
	echo "Usage: /etc/init.d/$TRANS_NAME {config|console|start|stop|restart|reload|force-reload}" >&2
	exit 1
	;;
esac

exit 0


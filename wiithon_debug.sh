#!/bin/bash

LOG_FILE=/tmp/wiithon_debug.log

/usr/games/wiithon --version > $LOG_FILE
lsb_release -a >> $LOG_FILE 2>/dev/null
echo "kernel: $(uname -r)" >> $LOG_FILE
/usr/bin/locale >> $LOG_FILE
/usr/share/wiithon/wiithon_autodetectar.sh >> $LOG_FILE
echo "================================================================" >> $LOG_FILE
export WIITHON_DEBUG=True
/usr/games/wiithon >> $LOG_FILE 2>&1

echo -e "\nPlease attach file /tmp/wiithon_debug.log to open a bug\n"


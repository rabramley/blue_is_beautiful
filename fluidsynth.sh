#!/bin/bash

if pgrep -x "fluidsynth" > /dev/null
then
echo fluidsynth already flowing
else
fluidsynth -si -p "fluid" -C0 -R0 -r48000 -d -f ./fluidconfig.txt -a alsa -m alsa_seq &
fi

sleep 3

exit
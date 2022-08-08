#!/bin/bash

if pgrep -x "fluidsynth" > /dev/null
then
echo fluidsynth already flowing
else
fluidsynth -si -p "fluid" -C0 -R0 -r48000 -d -f ./fluidconfig.txt -a alsa -m alsa_seq &
fi

sleep 3

mini=$(aconnect -o | grep "MINILAB")
mpk=$(aconnect -o | grep "MPKmini2")
mio=$(aconnect -o | grep "mio")

if [[ $mini ]]
then
aconnect 'Arturia MINILAB':0 'fluid':0
echo MINIlab connected
elif [[ $mpk ]]
then
aconnect 'MPKmini2':0 'fluid':0
echo MPKmini connected
elif [[ $mio ]]
then
aconnect 'mio':0 'fluid':0
echo Mio connected
else
echo No known midi devices available. Try aconnect -l
fi

cd fluidweb
node index.js
cd ..

exit
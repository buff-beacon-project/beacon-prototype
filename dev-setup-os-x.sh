#!/bin/sh

# exit when any command fails
set -e

# create a virtualbox virtual machine for the beacon
docker-machine create --driver virtualbox beacon-server

# stop the autorun
docker-machine stop beacon-server

# enable usb2.0 driver... requires VirtualBox Extension Pack
vboxmanage modifyvm beacon-server --usbohci on

# if using a different HSM key, figure out the vendor/product ids using:
# $ vboxmanage list usbhost

# add yubihsm device access
vboxmanage usbfilter add 0 --target beacon-server --name 'Yubico YubiHSM' --vendorid 0x1050 --productid 0x0030

# start the machine
docker-machine start beacon-server

echo "You will need to run this before running docker:"
echo 'eval "$(docker-machine env beacon-server)"'

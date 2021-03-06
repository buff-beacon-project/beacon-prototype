# beacon-prototype

# Specification

References in source code relate to https://nvlpubs.nist.gov/nistpubs/ir/2019/NIST.IR.8213-draft.pdf

# Setup

Install docker.
https://docs.docker.com/v17.09/engine/installation/

Run docker compose

```
$ docker-compose up
```

# Setup with HSM support on OS X / Windows

To get this working with docker on a mac/windows host machine, you need to run
docker in a virtual machine.

Install docker machine:

(on OS X)

```
$ brew install docker-machine
```

Then install virtual box:
https://www.virtualbox.org/wiki/Downloads

Then install the appropriate version of VirtualBox Extension Pack (same link).

Now you can run the helper script if you are on OS X:

```
$ bash ./dev-setup-os-x.sh
```

**OR** you can follow the instructions here: http://gw.tnode.com/docker/docker-machine-with-usb-support-on-windows-macos/
... with a slight modification: use command `$ vboxmanage modifyvm <vmname> --usbohci on`

You will need to ensure that the machine is running before starting the docker containers:

```
$ docker-machine start beacon-server
```

And in order to run docker, you will need to run the following every time you enter
a new console session:

```
$ eval "$(docker-machine env beacon-server)"
$ docker-compose up
```

# Tests

$ pipenv run python3 -m unittest discover

# TODO

[ ] check docker permissions and get rid of privileged: true
[ ] use https for communication with HSM??

# Spec changes

1. Pulse index must start at zero if first in chain
2. previous, hour, day, month, year are changed in favour of skipListAnchors, skipListLayerSize, skipListNumLayers
3. For conventional simplicity, chainIndex starts at 0

# References for development

* https://nvlpubs.nist.gov/nistpubs/ir/2019/NIST.IR.8213-draft.pdf
* https://developers.yubico.com/python-yubihsm
* https://github.com/coreos/fero
* http://gw.tnode.com/docker/docker-machine-with-usb-support-on-windows-macos/

* https://docs.timescale.com/

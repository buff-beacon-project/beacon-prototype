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

Firstly, install virtual box:
https://www.virtualbox.org/wiki/Downloads

Secondly, install the appropriate version of VirtualBox Extension Pack (same link).

Now you can run the helper script if you are on OS X:

```
$ bash ./dev-setup-os-x.sh
```

**OR** you can follow the instructions here: http://gw.tnode.com/docker/docker-machine-with-usb-support-on-windows-macos/
... with a slight modification: use command `$ vboxmanage modifyvm <vmname> --usbohci on`

In order to run docker, you will need to run the following every time you enter
a new console session:

```
$ eval "$(docker-machine env beacon-server)"
$ docker-compose up
```

# Tests

$ pipenv run python3 -m unittest discover

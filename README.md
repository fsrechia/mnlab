mnlab
=====

personal mininet lab experiments

mn version: 2.1.0
ovs-vsctl (Open vSwitch) 2.0.1
Compiled Feb 23 2014 14:42:32


Installing
==========

Installation steps were done using ubuntu 14.04.
Mininet's apt-get version is not the latest, but it is more convenient to install this way.

1. Install mininet and quagga:

Mininet should install ovs automatically.

apt-get install mininet
apt-get install quagga

2. Add zebra to user path. 

For all users, edit /etc/profile and append:

PATH=$PATH:/usr/lib/quagga/
export PATH

3. Set the 's' bit for quagga's daemons in order to be able to run them with any user:

chmod +s /usr/lib/quagga/

 


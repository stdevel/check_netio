check_netio
==========
``check_netio`` is a Nagios / Icinga plugin for checking power states of [Koukaan NETIO devices](http://www.koukaam.se/kkmd/products.php?cat_id=19).

This plugin is quite old (*~2012*), I'm planning to update it for [some reasons](https://github.com/stdevel/check_netio/issues/1).

Requirements
============
You need to have the ``netcat`` / ``nc`` binary installed.

Usage
=====
By default the plugin checks whether your defined power states matches the currently set states. It is also possible to check whether NTP is synchronized. Checking the NETIO is done using the **KShell** interface.

You need to specify the following parameters:

| Parameter | Description |
|:----------|:------------|
| 1. (``$1``) | Defines the hostname or IP address |
| 2. (``$2``) | Sets the KShell port (*e.g. 1234*) |
| 3. (``$3``) | Defines a valid user / administrator username |
| 4. (``$4``) | Sets the appropriate password |
| 5. (``$5``) | Defines the check mode; ``time`` for checking NTP state or the 4 port states (*0,1*) |

You can also specify particular cluster nodes that need to be connected to the quorum server. In this case the plugin will return ``CRITICAL`` events if one of those nodes are disconnected from the quorum server.

Examples
========
Check whether the NTP time is synchronized:
```
$ ./check_netio.sh 10.22.1.8 1337 admin password time
OK - time synchronized with SNTP server
```

Check whether power port states are matching with expectation (*Port 1 turned on, other ports turned off*):
```
$ ./check_netio.sh 10.22.1.8 1337 admin password 1000
OK: Port states matching
```

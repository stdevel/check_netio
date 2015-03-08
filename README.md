check_netio
==========
``check_netio`` is a Nagios / Icinga plugin for checking power states of [Koukaan NETIO devices](http://www.koukaam.se/kkmd/products.php?cat_id=19).

Requirements
============
I successfully tested the plugin with **NETIO-230A** and **NETIO-230B** devices. Most recent firmware version on newer product releases might not work (*see table below*).

Usage
=====
By default the plugin checks whether your defined power states matches the currently set states. It is also possible to check whether NTP is synchronized. Checking the NETIO is done using the **CGI** or **KShell** interface.

You need to specify the following parameters:

| Parameter | Description |
|:----------|:------------|
| `-d` / `--debug` | enable debugging outputs (*default: no*) |
| `-s` / `--hostname` | defines the device hostname |
| `-u` / `--use-kshell` | use KShell instead of CGI (*default: no*) |
| `-a` / `--authfile` | defines an auth file to use instead of shell variables |
| `-p` / `--kshell-port` | defines the KShell port (*default: 1234*) |
| `-y` / `--use-hash` | uses password hash instead of plain password (*default: no*) |
| `-g` / `--generate-hash` | generates a password hash and quits (*default: no*) |
| `-n` / `--check-ntp` | checks NTP synchronization state - requires KShell (*default: no*) |
| `-x` / `--port-state` | defines expected port states [*0=off, 1=on, ?=whatever*] |

Examples
========
Check whether the NTP time is synchronized:
```
$ ./check_netio.py -s mynetio -a authfile -n
OK - NTP state is synchronized
```

Check whether the NTP time is synchronized, specifying a different KShell port, login information is prompted:
```
$ ./check_netio.py -s mynetio -n -p 1337
Username: admin
Password:
CRITICAL - NTP NOT synchronized
```

Check whether the last port is turned on, login information is assigned using shell variables:
```
$ NETIO_LOGIN=admin NETIO_PASSWORD=pass ./check_netio.py -s mynetio -x ???1
WARNING - port difference detected: 4
```

Check all port states and also NTP synchronization state:
```
$ ./check_netio.py -s mynetio -x 0001 -n
Username: admin
Password:
OK - ports (0001) matching expectations (0001) - NTP synchronized
```

Firmware support
================
See the table below for tested firmware versions:

| Device | Firmware | Status |
|:-------|:---------|:-------|
| **230A** | [2.31](http://www.koukaam.se/kkmd/downloads.php?cat_id=18&download_id=1229) | working |
| **230A** | [2.32](http://www.koukaam.se/kkmd/downloads.php?cat_id=18&download_id=1314) | working |
| **230A** | [2.33](http://www.koukaam.se/kkmd/downloads.php?cat_id=18&download_id=1332) | working |
| **230A** | [2.34RC1](http://www.koukaam.se/kkmd/downloads.php?cat_id=6&download_id=1610) | working |
| **230B** | [3.12](http://www.koukaam.se/kkmd/downloads.php?cat_id=6&download_id=1693) | working |
| **230B** | [4.03](http://www.koukaam.se/kkmd/downloads.php?cat_id=6&download_id=1985) | working |
| **230B** | [4.05](http://www.koukaam.se/kkmd/downloads.php?cat_id=6&download_id=2109) | working |
| **230C** | [4.03](http://www.koukaam.se/kkmd/downloads.php?cat_id=6&download_id=1986) | *not tested* |
| **230C** | [4.05](http://www.koukaam.se/kkmd/downloads.php?cat_id=6&download_id=2110) | *not tested* |
| **230CS** | [4.03](http://www.koukaam.se/kkmd/downloads.php?cat_id=6&download_id=1987) | *not tested* |
| **230CS** | [4.05](http://www.koukaam.se/kkmd/downloads.php?cat_id=6&download_id=2111) | *not tested* |

Please let me know if you have tested the plugin on previously untested devices to complete the list!

Authentification options
========================
By default login information are prompted interactively - e.g.:
```
$ ./check_netio.py -s mynetio -n
Username:
Password:
```

If you want to make the script work unattended you might choose between one of the following options:

##Option 1: shell variables
Set those shell variables:
* **NETIO_LOGIN** - a username
* **NETIO_PASSWORD** - the appropriate password

You might also want to set the HISTFILE variable (*depending on your shell*) to hide the command including the password in the history:
```
$ HISTFILE="" NETIO_LOGIN=admin NETIO_PASSWORD=pass ./check_netio.py -s mynetio -n
```

##Option 2: auth file
A better possibility is to create a authfile with permisions **0600**. Just enter the username in the first line and the password in the second line:
```
$ cat authfile
admin
password
$ chmod 0600 authfile
```
Hand the path to the script:
```
$ ./check_netio.py -a myauthfile -s mynetio -n
```

The scripts will abort if the authfile has insecure permissions (*e.g. 0777*).

------------check_vmware_nsxt.py-----------

This script was created initally by https://exchange.icinga.com/netways/check_vmware_nsxt / https://github.com/NETWAYS/check_vmware_nsxt

The script required Python 3.8 which I didn't have installed within Nagios, so I changed it to not require Python 3.8

The rest of the script is the same, please find information in the links above.

Note: I do not take any credit for this script.


-----------check_nsxt_backup.py------------
NSX-T Backup Monitoring

https://www.virten.net/2021/03/nsx-t-backup-monitoring/ / https://github.com/fgrehl/virten-scripts/blob/master/python/check_nsxt_backup.py

Found this plugin from the link above and I wasn't able to get it working with the lastest version of NSX. I've completed some changes and it works now for me. I've also change it from minutes to hours for backup age

Note: I do not take any credit for this script.

import logging
import pprint
import time

logFormatter = logging.Formatter("[%(asctime)s] [%(module)-14.14s] [%(levelname)-5.5s] %(message)s")
log = logging.getLogger()

fileHandler = logging.FileHandler("script.log")
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(logging.DEBUG)
log.addHandler(fileHandler)
log.setLevel(logging.DEBUG)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
consoleHandler.setLevel(logging.INFO)
log.addHandler(consoleHandler)

log.info("Starting Test...")

from mdslib.switch import Switch
from mdslib.modules.vsan import Vsan
from mdslib.modules.devicealias import DeviceAlias

user = 'admin'
pw = 'nbv!2345'
ip_address = '10.126.94.107'
p = 8443

sw = Switch(
    ip_address=ip_address,
    username=user,
    password=pw,
    connection_type='https',
    port=p,
    timeout=30,
    verify_ssl=False)
pprint.pprint(sw.ipaddr)
pprint.pprint(sw.version)
pprint.pprint(sw.model)
print(sw.modules)
# pprint.pprint(sw.reload(module=1,timeout=330,copyrs=True))


print("Device Alias section ")
dah = DeviceAlias(sw)
print(dah.mode)
dah.mode = 'Ena'
print(dah.mode)

out = dah.create(name="Suhas", pwwn="aa:bb:cc:dd:ee:ff:00:11")
print(dah.is_device_alias_present(name="Suhas"))
print(dah.is_device_alias_present(name="Suhas1"))

dah.rename(oldname="Suhas", newname="Suhas1")
print(dah.is_device_alias_present(name="Suhas"))
print(dah.is_device_alias_present(name="Suhas1"))

dah.delete(name="Suhas1")
print(dah.is_device_alias_present(name="Suhas"))
print(dah.is_device_alias_present(name="Suhas1"))

out = dah.get_facts()
pprint.pprint(out)

# print("Vsan section ")
# print("------Getting vsan 20 object")
# v20 = Vsan(switch=sw, id=20)
#
# print("------Create vsan 20 with some name say V20")
# out = v20.create(name="V20")
# print("------Output of vsan 20 creation")
# print(out)
#
# print("------Add interface to vsan 20")
# v20.add_interfaces('fc1/32,fc1/24')
#
# print("------Print vsan 20 name")
# print(v20.name)
#
# print("------Change vsan 20 name")
# v20.create(name="20th Vsan")
#
# print("------Print vsan 20 name")
# print(v20.name)
#
# print("------Print vsan 20 id")
# print(v20.id)
#
# print("------Print vsan 20 state")
# print(v20.state)
#
# print("------suspend vsan 20")
# v20.suspend()
# time.sleep(10)
#
# print("------Print vsan 20 state")
# print(v20.state)
#
# print("------no suspend vsan 20")
# v20.suspend(False)
#
# print("------Print vsan 20 state")
# print(v20.state)
#
# print("------Print vsan 20 interfaces")
# print(v20.interfaces)
#
# print("------Print get all facts about vsan 20")
# print(v20.get_facts())
#
# print("------Getting vsan object with id 1")
# v1 = Vsan(switch=sw, id=1)
# print("------Print vsan name,id,state,interaces of vsan 1")
# print(v1.name)
# print(v1.id)
# print(v1.state)
# print(v1.interfaces)
#
# print("------Add interface to vsan 1")
# v1.add_interfaces('fc1/24')
#
# print("------Print vsan name,id,state,interaces and facts of vsan 20")
# print(v20.name)
# print(v20.id)
# print(v20.state)
# print(v20.interfaces)
# print(v20.get_facts())
#
# print("------Delete v20")
# out = v20.delete()
# print(out)

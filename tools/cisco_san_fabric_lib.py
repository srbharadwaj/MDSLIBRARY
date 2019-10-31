from mdslib.fabric import Fabric
import pprint
import logging

logFormatter = logging.Formatter("[%(asctime)s] [%(module)-14.14s] [%(levelname)-5.5s] %(message)s")
log = logging.getLogger()

fileHandler = logging.FileHandler("cisco_san_fabric_lib.log")
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(logging.DEBUG)
log.addHandler(fileHandler)
log.setLevel(logging.DEBUG)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
consoleHandler.setLevel(logging.INFO)
log.addHandler(consoleHandler)

log.info("Starting fabric discovery...")

seed_ip = '10.126.94.175'
username = 'admin'
password = 'nbv!2345'
port = 8443

f = Fabric("new")
if f.discover_all_switches_in_fabric(seed_switch_ip=seed_ip,
                                     username=username,
                                     password=password,
                                     connection_type='https',
                                     port=port,
                                     timeout=30,
                                     verify_ssl=False,
                                     discover_npv=True):

    swlist = f.discovered_switches
    print("List of switch ip and switch object")
    pprint.pprint(swlist)

    print("List of switch ip and switch version")
    for ip, swobj in swlist.items():
        print(ip, swobj.version)

from mdslib.connection_manager.errors import CLIError
import logging
from .zone import Zone

log = logging.getLogger(__name__)


class ZoneSet(object):
    def __init__(self, switch, vsan):
        self.__swobj = switch
        self.vsan = vsan
        self.__zoneObj = Zone(switch, vsan)

    @property
    def zonesets(self):
        out = self.get_facts()
        if out:
            return out.get('zoneset_details')
        return None

    @property
    def zoneset_names(self):
        retout = []
        out = self.zonesets
        if out is not None:
            for eachzs in out:
                retout.append(eachzs['zoneset_name'])
            return retout
        return None

    @property
    def active_zoneset(self):
        out = self.get_facts()
        if out:
            return out.get('active_zoneset_details')
        return None

    @property
    def active_zoneset_name(self):
        out = self.active_zoneset
        if out is not None:
            return out.get('zoneset_name')
        return None

    def create(self, name):
        log.debug("Create zoneset with name " + name + " in vsan " + str(self.vsan))
        cmd = "zoneset name " + name + " vsan " + str(self.vsan)
        return self.__zoneObj._send_zone_cmds(cmd)

    def delete(self, name):
        log.debug("Delete zone with name " + name + " in vsan " + str(self.vsan))
        cmd = "no zoneset name " + name + " vsan " + str(self.vsan)
        return self.__zoneObj._send_zone_cmds(cmd)

    def get_facts(self):
        log.debug("Getting zoneset facts")
        retoutput = {}
        temp = {}
        temp1 = {}
        out = self.__swobj.show("show zoneset vsan " + str(self.vsan))
        if out:
            out = out['TABLE_zoneset']['ROW_zoneset']
            if type(out) is list:
                temp1['zoneset_details'] = out
            if type(out) is dict:
                temp1['zoneset_details'] = [out]
            out1 = self.__swobj.show("show zoneset active vsan " + str(self.vsan))
            # print(out1)
            if out1:
                temp['active_zoneset_details'] = out1['TABLE_zoneset']['ROW_zoneset']
                # print(temp)
            retoutput = dict(temp1, **temp)
        return retoutput

    def add_members(self, name, members):
        cmds = self.__member_add_del(self.vsan, name, members)
        return self.__zoneObj._send_zone_cmds(cmds)

    def remove_members(self, name, members):
        cmds = self.__member_add_del(self.vsan, name, members, add=False)
        return self.__zoneObj._send_zone_cmds(cmds)

    def activate(self, name, action=True):
        cmd = "zoneset activate name " + name + " vsan " + str(self.vsan)
        if action:
            return self.__zoneObj._send_zone_cmds(cmd)
        else:
            cmd = "no " + cmd
            return self.__zoneObj._send_zone_cmds(cmd)

    @staticmethod
    def __member_add_del(vsan, name, members, add=True):
        cmdlist = []
        if add:
            log.debug("Trying to add zone members to zoneset with name " + name + " in vsan " + str(vsan))
        else:
            log.debug("Trying to remove zone members from zoneset with name " + name + " in vsan " + str(vsan))

        cmd = "zoneset name " + name + " vsan " + str(vsan)
        cmdlist.append(cmd)
        for eachmem in members:
            c = "member " + eachmem
            if add:
                cmd = c
            else:
                cmd = "no " + c
            cmdlist.append(cmd)
        cmds = " ; ".join(cmdlist)
        return cmds

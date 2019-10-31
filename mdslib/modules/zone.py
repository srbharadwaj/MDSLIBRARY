from mdslib.connection_manager.errors import CLIError
import logging

log = logging.getLogger(__name__)


class Zone(object):
    def __init__(self, switch, vsan):
        self.__swobj = switch
        self.vsan = vsan
        self._zones = None
        self.__rpc = None
        self.__method = u'cli_conf'

    @property
    def mode(self):
        facts_out = self.get_facts()
        return self.__get_mode(facts_out)

    @mode.setter
    def mode(self, mode):
        log.debug("Setting zone mode to " + mode + " for vsan " + str(self.vsan))
        cmd = "zone mode enhanced vsan " + str(self.vsan)
        if mode.lower() == 'enhanced':
            cmd = cmd
        elif mode.lower() == 'basic':
            cmd = "no " + cmd
        else:
            return self.__return_error("Invalid zone mode: " + str(mode), "basic")
        return self.__send_zone_cmds(cmd)

    @property
    def zone_names(self):
        retval = []
        allzones = self.zones
        if allzones is None:
            return None
        for eachrow in allzones:
            retval.append(eachrow['zone_name'])
        return retval

    @property
    def zones(self):
        facts_out = self.get_facts()
        zones = facts_out.get('zone_details')
        if not zones:
            return None
        elif type(zones) is dict:
            return [zones]
        else:
            return zones

    def create(self, name):
        log.debug("Create zone with name " + name + " in vsan " + str(self.vsan))
        cmd = "zone name " + name + " vsan " + str(self.vsan)
        return self.__send_zone_cmds(cmd)

    def delete(self, name):
        log.debug("Delete zone with name " + name + " in vsan " + str(self.vsan))
        cmd = "no zone name " + name + " vsan " + str(self.vsan)
        return self.__send_zone_cmds(cmd)

    def add_members(self, name, members):
        cmds = self.__member_add_del(self.vsan, name, members)
        return self.__send_zone_cmds(cmds)

    def remove_members(self, name, members):
        cmds = self.__member_add_del(self.vsan, name, members, add=False)
        return self.__send_zone_cmds(cmds)

    @staticmethod
    def __member_add_del(vsan, name, members, add=True):
        cmdlist = []
        if add:
            log.debug("Trying to add zone members to zone with name " + name + " in vsan " + str(vsan))
        else:
            log.debug("Trying to remove zone members from zone with name " + name + " in vsan " + str(vsan))

        cmd = "zone name " + name + " vsan " + str(vsan)
        cmdlist.append(cmd)
        for eachmem in members:
            for k, v in eachmem.items():
                c = "member " + k + " " + v
                if add:
                    cmd = c
                else:
                    cmd = "no " + c
                cmdlist.append(cmd)
        cmds = " ; ".join(cmdlist)
        return cmds

    def is_locked(self):
        facts_out = self.get_facts()
        if self.__locked_user(facts_out) is None:
            return True
        return False

    def clear_lock(self):
        cmd = "terminal dont-ask" + " ; clear zone lock vsan " + self.vsan + " ;  no terminal dont-ask"
        try:
            self.__swobj.show(cmd)
        except CLIError as c:
            return True, c.message
        return False, None

    @staticmethod
    def __get_mode(facts_out):
        if 'mode' in facts_out.keys():
            return facts_out['mode']
        return None

    def get_facts(self):
        log.debug("Getting zone facts")
        retoutput = {}
        temp = {}
        out = self.__swobj.show("show zone status vsan " + str(self.vsan))
        if out:
            # print(out)
            out = out['TABLE_zone_status']['ROW_zone_status']

            out1 = self.__swobj.show("show zone vsan " + str(self.vsan))
            if out1:
                temp['zone_details'] = out1['TABLE_zone']['ROW_zone']

            retoutput = dict(out, **temp)
        return retoutput

    @staticmethod
    def __locked_user(facts_out):
        if 'session' in facts_out.keys():
            lock = facts_out['session'].strip()
            if lock == "none":
                return None
            else:
                return lock

    def __send_zone_cmds(self, command):
        log.debug(command)
        facts_out = self.get_facts()
        mode = self.__get_mode(facts_out)

        lock_user = self.__locked_user(facts_out)
        if lock_user is not None:
            return self.__return_error("Switch has acquired zone lock by user " + lock_user, mode)
        try:
            o = self.__swobj.config(command, self.__rpc, self.__method)
            log.debug(o)
            if o is not None:
                # msg = o['msg']
                msg = o
                if msg:
                    if "Current zoning mode same as specified zoning mode" in msg:
                        log.debug(msg)
                    elif "Set zoning mode command initiated. Check zone status" in msg:
                        log.debug(msg)
                    elif "Enhanced zone session has been created" in msg:
                        log.debug(msg)
                    else:
                        return self.__return_error(msg, mode)
        except CLIError as c:
            return self.__return_error(c.message, mode)

        if mode.lower() == 'enhanced':
            cmd = "zone commit vsan " + str(self.vsan)
            try:
                o = self.__swobj.config(cmd, self.__rpc, self.__method)
                if o is not None:
                    msg = o
                    if msg:
                        if "Commit operation initiated. Check zone status" in msg:
                            pass
                        else:
                            return self.__return_error(msg, mode)
            except CLIError as c:
                if "No pending info found" in c.message:
                    pass
                else:
                    return self.__return_error(c.message, mode)

        return False, None

    def __return_error(self, message, mode):
        log.error(message)
        if mode is not None:
            if mode.lower() == 'enhanced':
                cmd = "clear zone lock"
                try:
                    self.__swobj.config(cmd, self.__rpc, self.__method)
                except CLIError as c:
                    return True, c.message
            return True, message

import logging
from mdslib.connection_manager.errors import CLIError

log = logging.getLogger(__name__)


class DeviceAlias(object):
    def __init__(self, sw):
        self.__swobj = sw

    @property
    def mode(self):
        facts_out = self.get_facts()
        return self.__get_mode(facts_out)

    @property
    def distribute(self):
        facts_out = self.get_facts()
        dis = self.__get_distribute(facts_out)
        if dis.lower() == 'enabled':
            return True
        else:
            return False

    @distribute.setter
    def distribute(self, distribute):
        if distribute:
            cmd = "device-alias database ; device-alias distribute"
            log.debug("Setting device alias mode to 'Enabled'")
        else:
            cmd = "device-alias database ; no device-alias distribute"
            log.debug("Setting device alias mode to 'Disabled'")
        return self.__send_device_alias_cmds(cmd)

    @mode.setter
    def mode(self, mode):
        log.debug("Setting device alias mode to " + mode)
        if mode.lower() == 'enhanced':
            cmd = "device-alias database ; device-alias mode " + mode.lower()
        elif mode.lower() == 'basic':
            cmd = "device-alias database ; no device-alias mode enhanced"
        else:
            return self.__return_error("Invalid device alias mode: " + str(mode))
        return self.__send_device_alias_cmds(cmd)

    def create(self, name, pwwn):
        log.debug("Creating device alias with args " + name + " " + pwwn)
        cmd = "device-alias database ; device-alias name " + name + " pwwn " + pwwn
        return self.__send_device_alias_cmds(cmd)

    def delete(self, name):
        log.debug("Deleteing device alias with args " + name)
        cmd = "device-alias database ; no device-alias name " + name
        return self.__send_device_alias_cmds(cmd)

    def rename(self, oldname, newname):
        log.debug("Renaming device alias with args " + oldname + " " + newname)
        cmd = "device-alias database ; device-alias rename " + oldname + " " + newname
        return self.__send_device_alias_cmds(cmd)

    def is_locked(self):
        facts_out = self.get_facts()
        if self.__locked_user(facts_out) is None:
            return True
        return False

    def clear_lock(self):
        cmd = "device-alias database ; clear device-alias session "
        try:
            self.__swobj.config(cmd)
        except CLIError as c:
            return True, c.message

    def is_device_alias_present(self, name):
        facts_out_da_entries = self.get_facts()['device_alias_entries']
        for eachentry in facts_out_da_entries:
            if eachentry['dev_alias_name'] == name:
                return True
        return False

    def get_facts(self):
        log.debug("Getting device alias facts")
        retoutput = {}
        out = self.__swobj.show("show device-alias database")
        num = out['number_of_entries']
        da = out['TABLE_device_alias_database']['ROW_device_alias_database']

        shdastatus = self.__swobj.show("show device-alias status")

        retoutput['number_of_entries'] = num
        retoutput['device_alias_entries'] = da

        return dict(retoutput, **shdastatus)

    def clear_database(self):
        raise NotImplemented  # TODO

    @staticmethod
    def __get_mode(facts_out):
        return facts_out['database_mode']

    @staticmethod
    def __get_distribute(facts_out):
        return facts_out['fabric_distribution']

    @staticmethod
    def __locked_user(facts_out):
        if 'Locked_by_user' in facts_out.keys():
            return facts_out['Locked_by_user']
        else:
            return None

    def __send_device_alias_cmds(self, command):
        log.debug(command)
        facts_out = self.get_facts()
        mode = self.__get_mode(facts_out)
        distribute = self.__get_distribute(facts_out)

        lock_user = self.__locked_user(facts_out)
        if lock_user is not None:
            return self.__return_error("Switch has acquired cfs device-alias lock by user " + lock_user, mode)

        try:
            o = self.__swobj.config(command)
            if o is not None:
                msg = o['msg']
                return self.__return_error(msg, mode)
        except CLIError as c:
            return self.__return_error(c.message, mode)

        if distribute:
            cmd = "terminal dont-ask ; device-alias database ; device-alias commit ; no terminal dont-ask "
            try:
                self.__swobj.config(cmd)
            except CLIError as c:
                return self.__return_error(c.message, mode)

        return False, None

    def __return_error(self, message, mode='enhanced'):
        log.error(message)
        if mode.lower() == 'enhanced':
            cmd = "terminal dont-ask ; device-alias database ; clear device-alias session ; no terminal dont-ask "
            try:
                self.__swobj.config(cmd)
            except CLIError as c:
                return False, c.message
        return True, message

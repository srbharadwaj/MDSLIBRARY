from mdslib.connection_manager.errors import CLIError
import logging

log = logging.getLogger(__name__)


class Vsan(object):
    def __init__(self, switch, id):
        self.__swobj = switch
        self.id = id

    @property
    def name(self):
        out = self.get_facts()
        if type(out) is not dict:
            return None
        else:
            return out['vsan_name']

    @property
    def state(self):
        out = self.get_facts()
        if type(out) is not dict:
            return None
        else:
            return out['vsan_state']

    @property
    def interfaces(self):
        out = self.get_facts()
        if type(out) is not dict:
            return None
        else:
            try:
                return out['vsan_interfaces']
            except KeyError:
                return None

    def create(self, name=None):
        cmd = "vsan database ; vsan " + str(self.id)
        if name is not None:
            cmd = cmd + " name '" + name + "'"
        try:
            self.__swobj.config(cmd)
        except CLIError as c:
            log.error(c)
            return True, c.message

        return False, None

    def delete(self):
        try:
            cmd = "terminal dont-ask ; " \
                  "vsan database ; " \
                  "no vsan " + str(self.id)
            self.__swobj.config(cmd)
        except CLIError as c:
            cmd = "no terminal dont-ask"
            self.__swobj.config(cmd)
            log.error(c)
            return True, c.message
        finally:
            cmd = "no terminal dont-ask"
            self.__swobj.config(cmd)
        return False, None

    def add_interfaces(self, interfaces):
        cmd = "vsan database ; vsan " + str(self.id) + " interface " + ','.join(interfaces)
        try:
            self.__swobj.config(cmd)
        except CLIError as c:
            if "membership being configured is already configured for the interface" in c.message:
                return False, None
            log.error(c)
            return True, c.message

        return False, None

    def suspend(self, state=True):
        cmd = "vsan database ; "
        if state:
            cmd = cmd + "vsan " + str(self.id) + " suspend"
        else:
            cmd = cmd + "no vsan " + str(self.id) + " suspend"
        try:
            self.__swobj.config(cmd)
        except CLIError as c:
            log.error(c)
            return True, c.message

        return False, None

    def get_facts(self):
        shvsan = self.__swobj.show("show vsan")
        shvsanmem = self.__swobj.show("show vsan " + str(self.id) + " membership")

        shvsan_req_out = {}
        shvsanmem_req_out = {}

        # Parse show vsan json output
        listofvsan = shvsan["TABLE_vsan"]["ROW_vsan"]
        for eachele in listofvsan:
            if str(eachele['vsan_id']) == str(self.id):
                shvsan_req_out = eachele
                break
        if not shvsan_req_out:
            log.debug("No info for vsan " + str(self.id))
            return None

        # Parse show vsan membership json output
        try:
            details = shvsanmem["TABLE_vsan_membership"]["ROW_vsan_membership"]['TABLE_vsan_interfaces'][
                'ROW_vsan_interfaces']
            if type(details) is dict:
                members = details['interface']
            else:
                members = [eachdetails['interface'] for eachdetails in details]
            shvsanmem_req_out = {'vsan_interfaces': members}
            if not shvsanmem_req_out:
                return shvsan_req_out
        except KeyError:
            return shvsan_req_out

        return dict(shvsan_req_out, **shvsanmem_req_out)

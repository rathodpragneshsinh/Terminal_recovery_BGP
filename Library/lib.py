from gxlib import API, ApiAuth, AsyncConnection
import re
from src.constant import KEY_PATH
from src.logger import logger


class Logs(object):

    def __init__(self, nms_ip : str, nms_username : str, nms_password : str, pp_username : str, terminal_name : str,did : str):
        """
        This class is written to capture the logs during the flight watch. It currently uses the terminal name to fetch the other paramters like
        the inet id, pp_gsr ip, pp_tpa ip, pp_na and pp_da ip along with their console port address,
        that is required to capture logs from pp_tpa, pp_na and pp_da and write into the respective files under the logs folder.

        Note: The script uses the private key to login into the pp. So, please replace the private key path in the 'private_key.yaml',
              under the config folder.

        :param nms_ip: The NMS ip
        :param nms_username: NMS username
        :param nms_password: NMS password
        :param pp_username: PP username
        :param terminal_name: Terminal name for which the logs need to be fetched.
        """
        self.nms_ip = nms_ip
        self.nms_username = nms_username
        self.nms_password = nms_password
        self.pp_username = pp_username
        self.terminal_name = terminal_name
        self.did = did
        auth = ApiAuth(nms_username, nms_password)
        self.api = API(nms_ip, auth)
        self.key_path = KEY_PATH
        self.proxy = None

    def get_terminal_id(self):
        return self.api.get_config(obj_type="terminal", query={"obj_name": self.terminal_name}, retrieve="obj_id")[0]

    def get_site_id(self, terminal_id : int | list[int]):
        """
        This method can be used to fetch the site id where the terminal is

        :param terminal_id: The object id of the terminal
        :return: The site id in which the terminal is.
        """
        site =  self.api.get_status(1702, element_id=terminal_id)
        return site[0]["value"][0]

    def get_inet_id(self, element_id : int | list[int]):
        """
        This method can be used to fetch the inet id of the terminal

        :param element_id: The object id of the terminal
        :return: The inet in which the terminal is
        """
        response = self.api.get_status(metric_id=1667, element_id=element_id)
        return response[0]["value"][0]

    def get_gsr_ip(self, site_id : str):
        """
        This method can be used to fetch the pp ip where the gsr process runs in that site

        :param site_id: The object id of the site
        :return: The pp gsr ip of that site
        """
        output = self.api.get_config(obj_type="protocolprocessorcluster", query={"obj_parentid" : site_id}, attributes_name=["ppgsraddress"])
        return output[0]["obj_attributes"]["ppgsraddress"]


    async def get_process_ip(self, gsr_ip : str, get_ip : str ="pp_tpa", inet : str = None):
        """
        This method currently supports to fetch the pp ip of the process pp_tpa, pp_na and pp_da from the pp_gsr process

        :param gsr_ip: The pp ip where the gsr process runs
        :param get_ip: The process ip which needs to be fetched from the gsr
        :param inet: The inet id
        :return: The ip of the process
        """
        #if gsr_ip.startswith("172."):
        #    self.proxy= AsyncConnection("10.238.232.5", username=self.pp_username, identity_file=self.key_path)
        #    await self.proxy.connect()
        async with AsyncConnection(gsr_ip, username=self.pp_username,
                               identity_file=self.key_path, process_username="admin",
                               process_password="iDirect", proxy=self.proxy) as conn:
            print(f"proxy is : {self.proxy}")
            print(conn)
            a = await conn.find_console_port(process_name="pp_gsr")
            if get_ip == "pp_tpa":
                pptpa_output = await conn.execute(commands=f"service_pool name RMT {self.did} show", console_port=a[0])
                #pattern = r'/*;(\d+.\d+.\d+.\d+);(\d+)'
                pattern = r"console_addr.*INET;(\d+.\d+.\d+.\d+);(\d+)"
                s = re.search(pattern, pptpa_output)
                if s is not None:
                    pp_tpa_ip = s.group(1)
                    pp_tpa_cp = s.group(2)
                    return (pp_tpa_ip, pp_tpa_cp)
            elif str(get_ip).lower() == "pp_da" or "pp_na":
                pp_na_da_output = await conn.execute(commands=f"service_pool name INET {inet} show", console_port=a[0])
                if get_ip == "pp_da":
                    pattern_da = "da_mnc_addr.*.;([0-255].*);"
                    return re.findall(pattern_da, pp_na_da_output)[0]
                else:
                    pattern_na = "na_mnc_addr.*.;([0-255].*);"
                    return re.findall(pattern_na, pp_na_da_output)[0]

    async def login_to_pp(self, pp_ip : str, process : str =None, inet_id : str="", find_cp : bool =False):
        """
        This method can be used to login into the PP with it's ip. It can also be used to fetch the console port of the process in that pp.
        Currently it is used to login into the pp incase of pp_tpa, pp_da and pp_na, finds console port incase of pp_da and pp_na provided the inet.

        :param pp_ip: The ip of the pp to login
        :param process: The process name
        :param inet_id: The inet id
        :param find_cp: True if needed to find the console port of the process, else False
        :return: The AsyncConnection class. In the case of console port to be fetched, it returns the class along with the console port
        """

        logger.info(f"{self.terminal_name} : PP ip is {pp_ip}")
        """enable proxy by uncommenting below lines"""
        #if pp_ip.startswith("172."):
            #self.proxy = AsyncConnection("10.238.232.5", username=self.pp_username,
            #                           identity_file=self.key_path)
            #await self.proxy.connect()
        pp_process = AsyncConnection(pp_ip, username=self.pp_username,
                                   identity_file=self.key_path,process_username="admin",
                                   process_password="iDirect", proxy= self.proxy)
        if find_cp:
            cp = await pp_process.find_console_port(process_name=process, inet=inet_id)
            return pp_process, str(cp[0])
        return pp_process



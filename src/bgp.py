import json
import re
from gxlib import AsyncAPI
from Library.lib import Logs
from logger import logger
from constant import dr

async def find_svn_sat_ip(api : AsyncAPI,obj : Logs,vrf_id):
    """
    This method will find sat0ip of svn name in config
    :param vrf_id:
    :param obj: Logs
    :param api: AsyncAPI
    :return: svn sat0ip
    """
    #https://10.238.232.45/api/2.0/config/terminalsvn?obj_parentid=6335551
    try:
        terminal_id = obj.get_terminal_id()
        svn_name = f"*COR-{vrf_id}"
        svn_sat_ip = await api.get_config("terminalsvn",query={"obj_parentid": terminal_id,"obj_name" : svn_name }, retrieve="sat0ip")
        return svn_sat_ip[0]
    except Exception as e:
        logger.error(f"{dr}Exception while fetching sat_ip of svn {e}")

async def check_bgp_status(svn_ip:str,obj:Logs,vrf_id : str , did : str,proxy = None) -> bool:
    """
    This method will log in to pp_rt_control and find BGP is Established or not
    :param proxy:
    :param svn_ip
    :param obj
    :param vrf_id
    :param did
    :return: True or False
    """
    try:
        terminal_id = obj.get_terminal_id()
        inet_id = obj.get_inet_id(terminal_id)
        site_id = obj.get_site_id(terminal_id)
        gsr_ip = obj.get_gsr_ip(site_id)
        pp_rt_ip, pp_tpa_cp = await obj.get_process_ip(gsr_ip, inet=inet_id, get_ip="pp_tpa")
        conn = await obj.login_to_pp(pp_rt_ip,"pp_rt_control")
        await conn.connect()
        pp_rt_cp = await conn.find_console_port(process_name="pp_rt_control")
        await conn.execute(f"rmt {did}",console_port= pp_rt_cp[0])
        await conn.execute(f"ip vrf {vrf_id}",console_port= pp_rt_cp[0])
        bgp_peer =await conn.execute("ip bgp opt peer",console_port= pp_rt_cp[0],prompt="End of table")
        print(f"bgp peer:{bgp_peer}")
        bgp_state = re.compile(f"{svn_ip}.*Est:*.up/up")
        match = bgp_state.search(bgp_peer)
        return True if match else False
    except Exception as e:
        logger.error(f"Exception while checking BGP state {e}")


async def write_json(file_path ,data : dict[str,str]):
    """

    :param file_path:
    :param data:
    :return:
    """
    try:
        with open(file_path,'w') as fd:
            json.dump(data,fd,indent=4)
    except Exception as e:
        logger.info(f"An unexpected error occurred: {e}")

async def read_json(file_path):
    """
    :param file_path:
    :return:
    """
    try:
        with open(file_path) as fp:
            return json.load(fp)
    except FileNotFoundError as e:
        logger.info(f"File is not present {file_path} ")
    except json.JSONDecodeError:
        logger.info(f"Error: The file {file_path} contains invalid JSON or is empty.")
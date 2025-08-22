from gxlib import AsyncAPI

from logger import logger
from constant import (
    TERMINAL_OPERATIONAL_STATE,
    ALT_PATTERN, TERMINAL_ALT, dr,
    TERMINAL_STATE_CHECK,
)
from  Library.lib import Logs
import re

alt_find = re.compile(ALT_PATTERN)
async def check_terminal_state(api : AsyncAPI,terminal_name : str):
    """
    This method will check terminal state
    :param terminal_name:
    :param api: AsyncAPI
    :return: if online return True offline return false
    """
    try:
        i = 0
        status = False
        while i < TERMINAL_STATE_CHECK:
            terminal = await api.get_config(
                "terminal",
                {"obj_name" : terminal_name},
                attributes_name=["mgmtipaddress", "ospassword"]
            )
            #logger.info(f'{dr} Terminal is : {terminal[0]["obj_name"]}')
            if terminal:
                obj_id = terminal[0]["obj_id"]
                terminal_status =await api.get_status([TERMINAL_OPERATIONAL_STATE, obj_id], element_id=obj_id)
                terminal_status = {i["metric_id"]: i["value"][0] for i in terminal_status}
                status = True if terminal_status[str(TERMINAL_OPERATIONAL_STATE)] == '1' else False
                if status:
                    break
                else:
                    i+=1
                    #await asyncio.sleep(3)
        return status
    except Exception as e:
        logger.error(f"{dr} {terminal_name} Not able to fetch terminal username and password {e}")

async def check_terminal_alt(obj : Logs,did : str,terminal : str):
    """
    this method will check terminal altitude is above or equal to threshold
    :param terminal:
    :param obj
    :param did terminal did
    :return: True is altitude is greater and equal to attitude or False
    """
    try:
        terminal_id = obj.get_terminal_id()
        inet_id = obj.get_inet_id(terminal_id)
        site_id = obj.get_site_id(terminal_id)
        gsr_ip = obj.get_gsr_ip(site_id)
        try:
            pp_tpa_ip, pp_tpa_cp = await obj.get_process_ip(gsr_ip, inet=inet_id, get_ip="pp_tpa")
            logger.info(f"pptpa_ip {pp_tpa_ip} pp_tpa_cp {pp_tpa_cp}")
        except TypeError :
            logger.info(f"{dr} {terminal} :issue while fetching ip's ")
            return False
        logger.info(f"{dr} {terminal} : pp_tpa ip : {pp_tpa_ip} console port {pp_tpa_cp}")
        pp_process = await obj.login_to_pp(pp_tpa_ip,process = "pp_tpa")
        await pp_process.connect()
        cmd = [f"rmt {did} ", "status please"]
        out = await pp_process.execute(cmd,console_port=pp_tpa_cp)
        try:
            terminal_alt = alt_find.findall(out)[0]
            logger.info(f"{dr} {terminal} :Terminal altitude is {terminal_alt}")
            return True if int(terminal_alt) >= int(TERMINAL_ALT) else False
        except IndexError:
            return False
    except Exception as e:
        logger.error(f"{dr} {terminal} There is as exception while fetching Terminal altitude {e}")
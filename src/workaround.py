import asyncio
from Library.lib import Logs
from constant import find_inet_sat_fom_beam_pattern, DRYRUN, dr
from logger import logger
global cur_sat_beam_inet_fom
from check_terminal_state import check_terminal_state
from gxlib import AsyncAPI


async def find_process_ip_with_cp(obj:Logs, process_name : str = "pp_tpa")-> tuple :
    """
    This method will take logs as argument and fine
    pp_tpa_ip and pp_tpa_cp and inet_id and return
    :param process_name: pp_tpa , pp_na , pp_da
    :param obj: Logs
    :param : process_name
    :return: tuple
    """
    try:
        terminal_id = obj.get_terminal_id()
        inet_id = obj.get_inet_id(terminal_id)
        site_id = obj.get_site_id(terminal_id)
        gsr_ip = obj.get_gsr_ip(site_id)
        if process_name.lower() == 'pp_tpa':
            pp_tpa_ip, pp_tpa_cp = await obj.get_process_ip(gsr_ip, inet=inet_id, get_ip=process_name)
            return pp_tpa_ip,pp_tpa_cp,inet_id
        if process_name.lower() == 'pp_na':
            pp_na_ip= await obj.get_process_ip(gsr_ip, inet=inet_id, get_ip=process_name)
            return pp_na_ip,inet_id
    except Exception as e:
        logger.error(f"Exception while finding process ip with cp {e}")

async def force_ucp_out(obj : Logs,did : str,api : AsyncAPI, terminal : str,proxy = None):
    """
    This method will loging to pp_tpa and run force ucp out and check terminal state
    :param proxy:
    :param obj:
    :param did:
    :param api:
    :param terminal:
    :return: True or False
    """
    pp_tpa_ip, pp_tpa_cp,inet_id = await find_process_ip_with_cp(obj)
    conn = await obj.login_to_pp(pp_tpa_ip,process = "pp_tpa")
    await conn.connect()
    await conn.execute(f"rmt {did}",console_port= pp_tpa_cp)
    if not DRYRUN:
        await conn.execute("force ucp out",console_port= pp_tpa_cp) #this is workaround command
    logger.info(f"{dr} {terminal} running command : force ucp out ")
    logger.info(f"{dr} {terminal} Check terminal is online after force ucp out")
    return await check_terminal_state(api,terminal)
            #will check terminal status return true if it out of network

async def find_beam_switch_candidate(geo_data,cur_inet,switch : str = "beam")->int:
    """
    This method will find correct candidate to do beam switch
    :param switch:
    :param geo_data:
    :param cur_inet:
    :return: inet_id
    """
    try:
        cur_sat_beam_inet_fom = ""
        inet_list = []
        for data in geo_data.split("\n"):
            match = find_inet_sat_fom_beam_pattern.search(data)
            if match:
                if match.group("inet") == cur_inet:
                    cur_sat_beam_inet_fom = (match.group("sat_name"),match.group("beam_id"),match.group("inet"),match.group("fom"))
                    logger.info(f"{dr} Current inet data : {cur_sat_beam_inet_fom}")
                else:
                    inet_list.append((match.group("sat_name"),match.group("beam_id"),match.group("inet"),match.group("fom")))
                    logger.info(f"{dr}All inet list :{inet_list}")
            for i in inet_list:
                if switch == "beam" and cur_sat_beam_inet_fom[0] == i[0] and cur_sat_beam_inet_fom[2] != i[2] and int(i[3]) == 0:
                    return i[2]
        for i in inet_list:
            if switch == "sat" and cur_sat_beam_inet_fom[0] != i[0] and int(i[3]) == 0:
                return i[2]
    except Exception as e:
        logger.error(f"Failed to find beam switch candidate {e}")

async def beam_switch(obj:Logs,did : str,api : AsyncAPI , terminal : str,switch_type : str = "beam"):
    """
    This method will do beam switch / sat switch
    :param switch_type:
    :param api:
    :param terminal:
    :param obj:
    :param did:
    :return:
    """
    try:
        pp_tpa_ip, pp_tpa_cp,inet_id = await find_process_ip_with_cp(obj)
        conn = await obj.login_to_pp(pp_ip=pp_tpa_ip, process="pp_tpa", inet_id=inet_id)
        await conn.connect()
        await conn.execute(f"rmt {did}",console_port= pp_tpa_cp)
        geo_data = await conn.execute("bs_ctrl geo_data",console_port= pp_tpa_cp)
        logger.info(f"{dr} {terminal} :geo _Data : {geo_data}")
        inet_to_switch = await find_beam_switch_candidate(geo_data,inet_id ,switch_type)
        logger.info(f"{dr} {terminal} :Inet to switch {inet_to_switch} ")
        if not DRYRUN:
            if inet_to_switch is None:
                await conn.execute(f"bs_ctrl switch {inet_to_switch}",console_port= pp_tpa_cp)
            else:
                logger.info(f"{dr} {terminal} couldn't find beam with FOM 0 in same or different satellite")
                return False
        logger.info(f"{dr} {terminal} running command : bs_ctrl switch {inet_to_switch}")
        #Need to terminal is up and latched with beam we have tried
        await asyncio.sleep(60)
        if await check_terminal_state(api, terminal):
            terminal_id = obj.get_terminal_id()
            if int(inet_to_switch) == int(obj.get_inet_id(terminal_id)):
                logger.info(f"Terminal beam switch to {inet_to_switch}")
                return True
            else:
                logger.info("Terminal didn't do beam switch successfully")
                return False
    except Exception as e:
        logger.error("Exception while doing beam switch {e}")
    #Need to thing abot validation
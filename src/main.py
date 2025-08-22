from logger import logger
from allocation import na_allocation_check
from check_terminal_state import (check_terminal_alt,
                                      check_terminal_state
                                      )
from gxlib import (AsyncAPI,
                   ApiAuth
                   )
from constant import (TERMINAL_ALT,
                          NMS_IP,
                          NMS_USERNAME,
                          NMS_PASSWORD,
                          PP_USERNAME,
                          TERMINAL_NAME,
                          VRF_ID,
                          dr
                          )
from Library.lib import Logs
from bgp import (find_svn_sat_ip ,
                 check_bgp_status,
                 read_json,
                 write_json)
import asyncio

from src.constant import json_path
from workaround import beam_switch,force_ucp_out,find_process_ip_with_cp

async def run(obj : Logs,did : str,api : AsyncAPI,terminal : str,vrf_id :str):
    status = await force_ucp_out(obj,did,api,terminal)
    if status:
        logger.info(f"{dr} {terminal} Terminal is online after force ucp out")
        await asyncio.sleep(60) #to make sure BGP established
        logger.info(f"{dr} : {terminal} :checking BGP status after force ucp out ")
        svn_ip = await find_svn_sat_ip(api, obj, vrf_id)
        logger.info(f"{dr} {terminal} :SVN ip : {svn_ip}")
        if await check_bgp_status(svn_ip, obj, vrf_id, did):
            logger.info(f"{dr} {terminal} :BGP is established")
            logger.info(f"{dr} {terminal}: force UCP out : Workaround successfully")
        else:
            logger.info(f"{dr} {terminal}: After fource ucp  BGP is not established will do beam switch now")
            bs_status = await beam_switch(obj,did,api,terminal)
            if bs_status:
                await asyncio.sleep(60)  # to make sure BGP established
                logger.info(f"{dr} : {terminal} :checking BGP status after Beam switch ")
                svn_ip = await find_svn_sat_ip(api, obj, vrf_id)
                logger.info(f"{dr} {terminal} :SVN ip : {svn_ip}")
                if await check_bgp_status(svn_ip, obj, vrf_id, did):
                    logger.info(f"{dr} {terminal} :BGP is established")
                    logger.info(f"{dr} {terminal}: Beam switch : Workaround successfully")
                else:
                    sat_status = await beam_switch(obj,did,api,terminal,switch_type= "sat")
                    if sat_status:
                        await asyncio.sleep(60)  # to make sure BGP established
                        logger.info(f"{dr} : {terminal} :checking BGP status after Sat switch ")
                        svn_ip = await find_svn_sat_ip(api, obj, vrf_id)
                        logger.info(f"{dr} {terminal} :SVN ip : {svn_ip}")
                        if await check_bgp_status(svn_ip, obj, vrf_id, did):
                            logger.info(f"{dr} {terminal} :BGP is established")
                            logger.info(f"{dr} {terminal}: Sat switch : Workaround successfully")
                        else:
                            logger.error(f"{dr} {terminal}: Workaround failed")
    else:
        logger.info(f"{dr} {terminal} after force ucp out terminal is not In network")

async def run_task(terminal: str, vrf_id: str):
    """
    This method serves as the main entry point and orchestrates the execution of all subsequent method calls.
    The overall logic flow is as follows:
    Initial Check:
        * Verify if the terminal is online and currently flying above the configured altitude.
        * If both conditions are met, proceed with further evaluations.

    Test Case 1: Terminal is online, BGP is established, but data is not passing
        * Checking data is passing nothing to do further
        * if data is not passing
            * The script initiates a forced UCP out for the terminal.
            * After the operation, check if data transmission is restored:
                * If yes, the workaround is considered successful.
                * If no, proceed to perform a beam switch:
                    * If data starts passing, the workaround is successful.
                    * If not, log the workaround as failed.

    Test Case 2: Terminal is online but flying below the configured altitude
        * No action is taken in this case.

    Test Case 3: Terminal is online, but BGP is not established
        * The script initiates a forced UCP out for the terminal.
        * After the operation, check if data transmission is restored:
            * If yes, the workaround is successful.
            * If no, proceed to perform a beam switch:
                * If data starts passing, the workaround is successful.
                * If not, log the workaround as failed.
    :param terminal:
    :param vrf_id:
    :param did:
    :return:
    """
    did = terminal.split("-")[1]
    obj = Logs(nms_ip=NMS_IP, nms_username=NMS_USERNAME, nms_password=NMS_PASSWORD, pp_username=PP_USERNAME,
               terminal_name=terminal,did=did)
    auth = ApiAuth(NMS_USERNAME, NMS_PASSWORD)
    api = AsyncAPI(NMS_IP, auth)
    '''
    If we can't see terminal with terminal altitude greater than TERMINAL_ALT than will not do anything 
    '''
    j_data = {}
    cur_inet = ""
    try:
        terminal_id = obj.get_terminal_id()
        cur_inet = obj.get_inet_id(terminal_id)
        j_data = await read_json(json_path / f"{terminal}.json")
        logger.info(f"starting j_data : {j_data} and cur_inet {cur_inet}")
        if j_data is None:
            terminal_id = obj.get_terminal_id()
            inet = obj.get_inet_id(terminal_id)
            data = {terminal: {"inet": inet, "count": 0}}
            await write_json(json_path / f"{terminal}.json", data)
            j_data = await read_json(json_path / f"{terminal}.json")
            logger.info(f"starting j_data : {j_data} and cur_inet {cur_inet}")
    except:
        pass
    try:
        if j_data is not None and j_data[terminal]["inet"] != cur_inet or j_data[terminal]["count"] == 0:
            if await check_terminal_state(api,terminal) and await check_terminal_alt(obj,did,terminal):
                logger.info(f"{dr} {terminal} :Terminal is online and flying over {TERMINAL_ALT}")
                svn_ip = await find_svn_sat_ip(api, obj,vrf_id)
                logger.info(f"{dr} {terminal} :SVN ip : {svn_ip}")
                if await check_bgp_status(svn_ip, obj,vrf_id , did):
                    # will check BGP state and update beam in json so all time no need to check
                    logger.info(f"{dr} {terminal} :BGP is established")
                    logger.info(f"{dr} {terminal} :proceed with checking demand and allocation")
                    pp_na_ip, inet = await find_process_ip_with_cp(obj, "pp_na")
                    na_allocation_status = await na_allocation_check(obj, (pp_na_ip, inet), did, check_data=5)
                    data = {terminal: {"inet": inet, "count": 1}}
                    await write_json(json_path / f"{terminal}.json", data)
                    if na_allocation_status:
                        logger.info(f"{dr} {terminal} :Data is passing nothing To do")
                    else:
                        logger.info(f"{dr} {terminal} :Data is not passing will processed with force UCP out")
                        await run(obj,did,api,terminal,vrf_id)
                else:
                        await run(obj,did,api,terminal,vrf_id)
            else:
                logger.info(f"{dr} {terminal} :Terminal is offline or it is flying below {TERMINAL_ALT}")
        else:
            logger.info(f"{dr} {terminal} :Skipping BGP state check as there is not inet change")
    except Exception as e:
        logger.info(f"There is error while fetching data {e}")

async def run_thread():
    tasks = [asyncio.create_task(run_task(terminal,vrf)) for terminal,vrf in zip(TERMINAL_NAME,VRF_ID)]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    logger.info(f"Done tasks: {len(done)}, Pending tasks: {len(pending)}")
    print(f"Done tasks: {len(done)}, Pending tasks: {len(pending)}")

async def main():
    while True:
        await run_thread()

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
from Library.lib import Logs
from constant import na_pattern, BASIC_DEMAND
from logger import logger


async def na_allocation_check(obj : Logs, pp : tuple[str,str] ,did : str,check_data : int , proxy = None):
    """
    This method will run command network alloc | grep {did} command on pp_na
    get output from that and filtering demand and allocation
    :param proxy:
    :param check_data:
    :param obj:
    :param pp:
    :param did:
    :return: True or False
    """
    try:
        pp_na_ip , inet = pp
        demand = ""
        conn = await obj.login_to_pp(pp_ip=pp_na_ip, process="pp_na")
        await conn.connect()
        pp_na_cp = await conn.find_console_port(process_name="pp_na",inet=inet)
        for i in range(check_data):
            out = await conn.execute(commands=f"network alloc | grep {did}", console_port=pp_na_cp[0])
            for i in out.splitlines():
                if "VR(3)" in i:
                    demand = na_pattern.findall(i)
                    print(demand)
            await asyncio.sleep(1)
        try:
            demand_kbps = (int(demand[0][0]) * 8 ) / 1000
            print(demand_kbps)
            return True if int(demand_kbps) > int(BASIC_DEMAND) else False
        except Exception as e:
            return False
    except Exception as e:
        logger.error(f"Exception while getting allocation {e}")
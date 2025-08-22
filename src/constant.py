import yaml
from pathlib import Path
import os
import re
import dotenv


dotenv.load_dotenv()

CWD =Path(__file__).parent.parent.resolve()
file_path = CWD / "config" /"config.yml"

json_path = CWD / "terminal_inet"

with open(file_path,"r") as fd:
    CONFIG = yaml.load(fd,yaml.SafeLoader)

NMS_IP = CONFIG["NMS_IP"]
NMS_USERNAME = os.getenv("NMS_USERNAME")
NMS_PASSWORD = os.getenv("NMS_PASSWORD")
PP_USERNAME =   os.getenv("PP_USERNAME")
KEY_PATH = os.getenv("KEY_PATH")
PROCESS_USERNAME  = os.getenv("PROCESS_USERNAME")
PROCESS_PASSWORD = os.getenv("PROCESS_PASSWORD")
ROOT_PASSWORD= os.getenv("ROOT_PASSWORD")
TERMINAL_NAME = CONFIG["Terminal_name"]
TERMINAL_ALT = CONFIG["terminal_altitude"]
VRF_ID = CONFIG["vrf_id"]
DRYRUN = CONFIG["dryrun"]
BASIC_DEMAND = CONFIG["basic_demand"]
TERMINAL_OPERATIONAL_STATE = 1668
TERMINAL_STATE_CHECK = 5
ALT_PATTERN = "Alt: (.*.) m"
#DID = TERMINAL_NAME.split("-")[1]
find_inet_sat_fom_beam_pattern = re.compile(r"sat.domain.\[(?P<sat_name>\w+)]"
                                            r".*beam.\[(?P<beam_id>\d+)]"
                                            r".*net.\[(?P<inet>\d+)]"
                                            r".*fom.\[(?P<fom>\d+)]"
                                            )
na_pattern = re.compile("0x\S+.\s+(?P<demand>.\d*\S+).\s+(?P<allocation>.\d*\S+)")

dr = f'{"Dryrun:"if DRYRUN else ""}'




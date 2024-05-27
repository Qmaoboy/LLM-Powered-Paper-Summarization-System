from queue import Queue
import sys,logging
sys.path.append("./CLIP")
import torch,gc
import yaml
from tqdm import tqdm
import threading as th
from lib.utilized import *
import argparse
from lib.gpt_worker import GPT_Analysis_
from lib.mysql_class import sql_operater
from lib.mysql_class import mysql_db_client
import lib.logger as logger
import datetime
os.makedirs('log', exist_ok=True)
logger = logger.setup_logger(f'app/lib/log/{datetime.datetime.now().strftime("%Y-%m-%d_%H")}_backend.log')


with open('lib/config/config.yaml', 'r') as yamlfile:
    config = yaml.safe_load(yamlfile)
logger.info(f'Version {config["MainConfig"]["version"]}')

if __name__=="__main__":
    print("123")
    parser = argparse.ArgumentParser(description='Process tasks.')
    parser.add_argument('task', type=str, choices=['GPT_gen', 'sql_Action', 'End'], help='Task to perform')
    kwargs = parser.parse_args()

    if kwargs.task == 'GPT_gen':
        GPT_Analysis_(config,set_Target_list())
    elif kwargs.task == 'sql_Action':
        sql_operater(config)
    else:
        logger.error('Invalid task specified.')


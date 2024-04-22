from queue import Queue
import sys,logging
sys.path.append("./CLIP")
import torch,gc
import yaml
from tqdm import tqdm
import threading as th
from utilized import *
import argparse
from gpt_worker import GPT_Analysis_
from mysql_class import sql_operater
import shared_logger

logger = shared_logger.setup_logger('log/backend.log')


with open('backend/app/lib/config/config.yaml', 'r') as yamlfile:
    config = yaml.safe_load(yamlfile)

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Process tasks.')
    parser.add_argument('task', type=str, choices=['GPT_gen', 'sql_Action', 'End'], help='Task to perform')
    kwargs = parser.parse_args()

    if kwargs.task == 'GPT_gen':
        logger.info('Starting GPT_gen task...')
        GPT_Analysis_(config,set_Target_list())
    elif kwargs.task == 'sql_Action':
        logger.info('Starting sql_Action task...')
        sql_operater(config)
    else:
        logger.error('Invalid task specified.')



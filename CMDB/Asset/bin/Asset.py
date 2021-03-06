'''
    Asset.py
    Written By Kyle Chen
    Version 20190411v1
'''

## import buildin pkgs
import re
import os
import sys
import logging
import pandas as pd
from logging.handlers import RotatingFileHandler

## get workpath
workpath = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

## append workpath to path
sys.path.append("%s/lib" % (workpath))

## import priviate pkgs
from Config import Config
from Lock import Lock
from SendData import SendData

## Asset Class
class Asset(object):
    ## initial function
    def __init__(self):
        ## set priviate values
        self.config = Config(workpath)
        self.pid = os.getpid()
        self.pname = 'Asset.py'

        ## logger initial
        self.loggerInit()

        ## lock initial
        self.lockObj = Lock(
            self.pname,
            self.pid,
            self.config.LOCK_DIR,
            self.config.LOCK_FILE,
            self.logger)

        ## debug output
        self.logger.debug('Asset Initial Start')
        self.logger.debug('[SYS_CIS][%s]' % (self.config.SYS_CIS))
        self.logger.debug('[SYS_SAVE_CSV][%s]' % (self.config.SYS_SAVE_CSV))
        self.logger.debug('[SYS_CSV_DIR][%s]' % (self.config.SYS_CSV_DIR))
        self.logger.debug('[MQ_SERVERS][%s]' % (self.config.MQ_SERVERS))
        self.logger.debug('[MQ_PORT][%s]' % (self.config.MQ_PORT))
        self.logger.debug('[MQ_QUEUE][%s]' % (self.config.MQ_QUEUE))
        self.logger.debug('[SUBPROC_SCRIPTSDIR][%s]' % (self.config.SUBPROC_SCRIPTSDIR))
        self.logger.debug('[SUBPROC_TIMEOUT][%s]' % (self.config.SUBPROC_TIMEOUT))
        self.logger.debug('[LOCK_DIR][%s]' % (self.config.LOCK_DIR))
        self.logger.debug('[LOCK_FILE][%s]' % (self.config.LOCK_FILE))
        self.logger.debug('[LOG_DIR][%s]' % (self.config.LOG_DIR))
        self.logger.debug('[LOG_FILE][%s]' % (self.config.LOG_FILE))
        self.logger.debug('[LOG_LEVEL][%s]' % (self.config.LOG_LEVEL))
        self.logger.debug('[LOG_MAX_SIZE][%s]' % (self.config.LOG_MAX_SIZE))
        self.logger.debug(
            '[LOG_BACKUP_COUNT][%s]' %
            (self.config.LOG_BACKUP_COUNT))
        self.logger.debug('Asset Initial Done')

    ## initial logger
    def loggerInit(self):
        self.logger = logging.getLogger("Asset")

        try:
            log_level = getattr(logging, self.config.LOG_LEVEL)

        except BaseException:
            log_level = logging.NOTSET

        self.logger.setLevel(log_level)

        fh = RotatingFileHandler(
            self.config.LOG_FILE,
            mode='a',
            maxBytes=self.config.LOG_MAX_SIZE,
            backupCount=self.config.LOG_BACKUP_COUNT)
        fh.setLevel(log_level)

        ch = logging.StreamHandler()
        ch.setLevel(log_level)

        formatter = logging.Formatter(
            '[%(asctime)s][%(name)s][%(levelname)s] %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

        return(True)

    ## getObj from input args
    def getObj(self, module_name, class_name, *args, **kwargs):
        module_meta = __import__(module_name, globals(), locals(), [class_name])
        class_meta = getattr(module_meta, class_name)
        obj = class_meta(*args, **kwargs)

        return(obj)

    ## trans list data to dict
    def list2df(self, data):
        result = {}
        cols = data[0]
        data = data[1:]
        df = pd.DataFrame(data, columns = cols) 

        return(df)

    ## save to csv file
    def saveCSV(self, ci_name, data):
        df = self.list2df(data)
        df.to_csv('{}/{}.csv'.format(self.config.SYS_CSV_DIR, ci_name), index = False, sep = '|')
        return(True)

    ## send data to MQ
    def sendData(self):
        sendDataObj = SendData(self.logger, self.config, self.config.SYS_CIS)
        sendDataObj.run()
        return(True)

    ## run asset function
    def run(self):
        self.logger.debug('Getting Asset Data Start')

        ## auto import libs
        CIObj_dict = {}
        for l in self.config.SYS_CIS:
            CIObj_dict[l] = self.getObj(l, l, self.logger, self.config)
            self.logger.debug('[CIObj_dict][{}]'.format(l))

        ## get CIs data and save them in csv
        for ci_name in CIObj_dict:
            self.logger.debug('[call][{}]'.format(ci_name))
            csv_data = CIObj_dict[ci_name].getData()
            self.saveCSV(ci_name, csv_data)

        self.logger.debug('Getting Asset Data Done')

        ## send data to MQ
        self.sendData()

        ## release lock
        self.lockObj.release()

        return(True)

## run it
assetObj = Asset()
assetObj.run()

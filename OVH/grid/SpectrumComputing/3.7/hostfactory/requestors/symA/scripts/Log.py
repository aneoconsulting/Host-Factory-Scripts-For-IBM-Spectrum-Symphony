#!/usr/bin/python

# -*- coding: utf-8 -*-

import logging.handlers
import logging

class Log:
   
    logger = None
    
    @staticmethod
    def init (filePath, logLevel , logName): # constructor
        if Log.logger == None:

            Log.logger = logging.getLogger(logName)
            handler = logging.handlers.RotatingFileHandler(filePath, maxBytes=1024*1000, backupCount=5)
            handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s:%(message)s'))
            Log.logger.addHandler(handler)
            
            if logLevel == "DEBUG":
                Log.logger.setLevel(logging.DEBUG)
            elif logLevel == "TRACE":
                Log.logger.setLevel(logging.DEBUG)
            elif logLevel == "INFO":
                Log.logger.setLevel(logging.INFO)
            elif logLevel == "WARNING":
                Log.logger.setLevel(logging.WARNING)
            elif logLevel == "ERR":
                Log.logger.setLevel(logging.ERROR)
            elif logLevel == "ERROR":
                Log.logger.setLevel(logging.ERROR)
            else:
                Log.logger.setLevel(logging.WARNING)

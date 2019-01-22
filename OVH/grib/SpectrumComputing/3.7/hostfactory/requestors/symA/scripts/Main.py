#!/usr/bin/python

# -*- coding: utf-8 -*-

"""
Output: a string with format: retcode retval
    - if retcode = 0, then retval is the interface output
    - if retcode != 0, then retval is expect to be error message
"""

import json
import subprocess
import datetime
import gettext
import os, sys, socket, getopt
from Log import Log

requestor_name = 'symA'
log_filename = requestor_name + '-requestor.log'
failtime_temp_file = 'ego_failure_time.txt'

"""
Implemented policies: User needs to do the following steps to add his own policies
     - Update the policy in <requestor_name>req_policy_config.json
     - Under <requestor_name>req_config.json, change the scaling_policy (or host_return_policy in case of adding return policy) to match the policy you have created
     - Add the prober implementation to policy under this script, then update the list of implemented policies below 
"""
implemented_scaling_policies = ["throughput"]
implemented_return_policies = ["lazy","immediate"]
failover_errors = ["Cannot connect to grid or grid simulation component","Unable to contact IBM Spectrum Symphony system","Unable to get an entry point to the IBM Spectrum Symphony system"]

#gettext.bindtextdomain("messages_python", os.environ.get('HF_TOP', '') + '/nls')
gettext.bindtextdomain("messages_python", './nls')
gettext.textdomain("messages_python")
_ = gettext.gettext

class main:
    opt_getDemandRequests = False
    opt_getReturnRequests = False
    jsonType = "f"
    policyName = ""
    warmup_time = 60
    threshold = 100
    slotToCores = 1
    slotToRam = 1000
    return_history_expiry_time = 60
    unavailable_host_timeout = 30
    max_cores_per_hour = 0
    ego_host_startup_time = 5
    ego_failover_timeout = 10
    FailoverState =  False
    DemandFormat = 3

    def __error(self, errmsg, *args):
            Log.logger.error(errmsg % args)
            print(errmsg % args)
            sys.exit(1)

    def __init__(self, argv):
        
        if len(argv) == 4:
            self.jsonType = argv[3]

        if len(argv) > 4:
            #log error input
            print (_('The number of input parameters is not correct'))
            sys.exit(1)

        self.homeDir = argv[1]
        if not os.path.isdir(self.homeDir):
            print(_('%s is not a valid host requestor directory') % self.homeDir)
            sys.exit(1)

        self.jsonIn = argv[2]

        # get hostfactory top dir
        env_var = dict(os.environ)
        self.hfTopDir = env_var.get('HF_TOP', '')
        if self.hfTopDir is None or len(self.hfTopDir) == 0 or not os.path.isdir(self.hfTopDir):
            print(_('HF_TOP is not set in env or HF_TOP: %s is not a directory') % self.hfTopDir)
            sys.exit(1)

        self.hfWorkDir = env_var.get('HF_WORKDIR', '')
        if self.hfWorkDir is None or len(self.hfWorkDir) == 0 or not os.path.isdir(self.hfWorkDir):
            print(_('HF_WORKDIR is not set in env or HF_WORKDIR: %s is not a directory') % self.hfWorkDir)
            sys.exit(1)

        #get hostfactory conf dir
        self.hfConfDir = env_var.get('HF_CONFDIR', '')  + "/requestors/" + requestor_name + "/conf/"
        if self.hfConfDir is None or len(self.hfConfDir) == 0 or not os.path.isdir(self.hfConfDir):
            print(_('HF_CONFDIR is not set in env HF_CONFDIR: %s is not a directory') % self.hfConfDir)
            sys.exit(1)

        #get hostfactory log dir
        self.hfLogDir = env_var.get('HF_LOGDIR', '')
        if self.hfLogDir is None or len(self.hfLogDir) == 0 or not os.path.isdir(self.hfLogDir):
            self.hfLogDir = self.hfTopDir + '/log' 
            if not os.path.isdir(self.hfLogDir):
                print(_('HostFactory log directory: %s does not exist') % self.hfLogDir)
                sys.exit(1)

        logLevel = env_var.get('HF_LOGLEVEL', '')
        if logLevel is None or len(logLevel) == 0 :
            logLevel = 'INFO'

        logLevel = logLevel.replace("LOG_","")
        
        host_name = socket.gethostname()
        log_file_path = self.hfLogDir + '/' + log_filename + '.' + str(host_name)  
               
        # get log level (??) 

        try:
            opts, args = getopt.getopt(argv, "dr", ["getDemandRequests", "getReturnRequests"])
        except getopt.GetoptError:
            print (_("GetoptError"))
            sys.exit(1)

        logName = ''
        for opt, arg in opts:
            if opt in ("-d", "--getDemandRequests"):
                self.opt_getDemandRequests = True
                logName = 'DEMAND REQUEST'
            if opt in ("-r", "--getReturnRequests"):
                self.opt_getReturnRequests = True
                logName = 'RETURN REQUEST'
        Log.init(log_file_path, logLevel , logName)


    """
    Read field value as an integer
    """
    def readField(self, decoded,fieldName):
        startingPoint = decoded.find(fieldName)
        if startingPoint < 0 :
            return startingPoint
        result = int(float(decoded[startingPoint:].split("\n")[0].split(":")[1].strip().split(" ")[0]))
        return result

    def validateVariable(self, fieldName, container, mandatory, numeric, conf_file, defaultValue = 0):
        try:
            firsttemp = container[fieldName]
        except:
            if mandatory is True :
                Log.logger.error(_('%s is mandatory in %s') %(fieldName,conf_file))
                sys.exit(1)
            else :
                Log.logger.warning(_('Unable to find %s. Default value is used instead') %(fieldName))
                return False
            
        if numeric == 1: # Allowed values are 1 for num, 2 for array, 0 for string, -1 to skip checking
            try:
                temp = int(container[fieldName])
            except:
                if mandatory is True :
                    Log.logger.error(_('%s has to be numeric in %s') %(fieldName,conf_file))
                    sys.exit(1)
                
                else :
                    Log.logger.warning(_('%s has to be numeric. Default value of %d is used instead') %(fieldName,defaultValue))
                    return False
        elif numeric == 0 and not container[fieldName]: # Check if field is a string
            if mandatory is True :
                Log.logger.error(_('%s is mandatory in %s') %(fieldName,conf_file))
                sys.exit(1)
            else :
                Log.logger.warning(_('%s is not valid string') %(fieldName))
                return False
        elif numeric == 2 : # Check if field is list
            if not isinstance(container[fieldName], list) : 
                if mandatory is True :
                    Log.logger.error(_('%s is mandatory list in %s') %(fieldName,conf_file))
                    sys.exit(1)
                else :
                    Log.logger.warning(_('%s is not valid list. Default value is used instead') %(fieldName))
                    return False
            elif len(container[fieldName]) == 0 :
                bigError = _('%s list is empty.') %(fieldName)
                if fieldName == "resource_groups" :
                    Log.logger.warning(_('%s Specify one or more resource groups; otherwise, the ComputeHosts resource group will be used by default.') %(bigError))
                elif fieldName == "resource_plans" :
                    Log.logger.debug(_('%s Specify one or more resource plans; otherwise, the resource plan associated with the resource group in the resource_groups parameter is used. For multidimensional scheduling, you must specify one or more resource plans.') %(bigError))
                else :
                    Log.logger.warning(bigError)
                return False
        
        return True

    """
    Read policy configuration file and set policy
    """
    def readPolicyConfig(self):
        conf_file = self.hfConfDir + requestor_name + "req_policy_config.json"
        if not os.path.isfile(conf_file):
            print(_('Requestor %s policy config file: %s does not exist') % (requestor_name, conf_file))
            Log.logger.error(_('Requestor %s policy config file: %s does not exist') % (requestor_name, conf_file))
            sys.exit(1)

        with open(conf_file) as data_file:
            configJson = json.load(data_file)
            
        data_file.closed
        
        self.validateVariable("scaling_policy", configJson, True, -1, conf_file)

        for policy in configJson["scaling_policy"] :
            self.validateVariable("name", policy, True, 0, conf_file)
            if policy["name"] == self.scalingPolicyName :
                self.history_expiry_time = policy.get("history_expiry_time")
                if self.validateVariable("history_expiry_time", policy, False, 1, conf_file, 60) is False :
                    self.history_expiry_time = 60
                elif int(self.history_expiry_time) > 1440 or int(self.history_expiry_time) <= 0 :
                    Log.logger.warning(_('%s is out of bounds. Default value of %d is used instead') %("history_expiry_time",60))
                    self.history_expiry_time = 60

                self.warmup_time = policy.get("warmup_time")
                if self.validateVariable("warmup_time", policy, False, 1, conf_file, 5) is False :
                    self.warmup_time = 5                    
                elif int(self.warmup_time) >= self.history_expiry_time or int(self.warmup_time) <= 0:
                    Log.logger.warning(_('%s is out of bounds. Default value of %d is used instead') %("warmup_time",5))
                    self.warmup_time = 5
                if self.history_expiry_time <= self.warmup_time :
                    self.history_expiry_time = 2 * self.warmup_time 
                    Log.logger.warning(_('Expiry time cannot be less than warmup time. Setting expiry time to %d minutes instead')%(self.history_expiry_time))

                self.ego_host_startup_time = policy.get("ego_host_startup_time")
                if self.validateVariable("ego_host_startup_time", policy, False, 1, conf_file, 0) is False :
                    self.ego_host_startup_time = 5
                elif int(self.ego_host_startup_time) > 10 or int(self.ego_host_startup_time) < 0:
                    Log.logger.warning(_('%s is out of bounds. Default value of %d is used instead') %("ego_host_startup_time",5))
                    self.ego_host_startup_time = 5

                self.ego_failover_timeout = policy.get("ego_failover_timeout")
                if self.validateVariable("ego_failover_timeout", policy, False, 1, conf_file, 0) is False :
                    self.ego_failover_timeout = 10  
                elif int(self.ego_failover_timeout) <= 5:
                    Log.logger.warning(_('%s is out of bounds. Default value of %d is used instead') %("ego_failover_timeout",10))
                    self.ego_failover_timeout = 10

                self.max_cores_per_hour = policy.get("max_cores_per_hour")
                if self.validateVariable("max_cores_per_hour", policy, False, 1, conf_file, 0) is False :
                    self.max_cores_per_hour = 0                    
                elif int(self.max_cores_per_hour) > 10000 or int(self.max_cores_per_hour) < 0:
                    Log.logger.warning(_('%s is out of bounds. Default value of %d is used instead') %("max_cores_per_hour",0))
                    self.max_cores_per_hour = 0

                self.validateVariable("desired_task_complete_duration", policy, True, 1, conf_file)
                self.threshold = int(policy["desired_task_complete_duration"])
                if self.threshold > 1440 or self.threshold <= 0 :
                    Log.logger.warning(_('%s is out of bounds. Default value of %d is used instead') %("desired_task_complete_duration",10))
                    self.threshold = 10
                   
                self.active_task_moving_avg = policy.get("active_task_moving_avg")
                if self.validateVariable("active_task_moving_avg", policy, False, 1, conf_file, 5) is False :
                    self.active_task_moving_avg = 5
                elif int(self.active_task_moving_avg) > self.history_expiry_time :
                    Log.logger.warning(_('%s is out of bounds. History expiry time value of %d is used instead') %("active_task_moving_avg",self.history_expiry_time))
                    self.history_expiry_time = self.history_expiry_time                    
                elif int(self.active_task_moving_avg) <= 0 :
                    Log.logger.warning(_('%s is out of bounds. Default value of %d is used instead') %("active_task_moving_avg",5))
                    self.active_task_moving_avg = 5                    
                return True
        return False


    def readReturnPolicyConfig(self):
        #If no return policy, then use the default lazy policy
        #if policy is immediate, then set immediate policy
        #Otherwise, read the policy from policy file.
        #All values here are in minutes
        self.billCycle = 60
        self.returnWindow = 10
        if self.returnPolicyName is None or self.returnPolicyName == '':
            self.returnPolicyName = "lazy"
            Log.logger.info(_('No return policy has been defined. Default lazy policy is used.'))
        elif self.returnPolicyName == "immediate" :
            self.billCycle = 0
            self.returnWindow = 0
            return True
        
        conf_file = self.hfConfDir + requestor_name + "req_policy_config.json"
        if not os.path.isfile(conf_file):
            print(_('Requestor %s policy config file: %s does not exist') % (requestor_name, conf_file))
            Log.logger.error(_('Requestor %s policy config file: %s does not exist') % (requestor_name, conf_file))
            sys.exit(1)

        with open(conf_file) as data_file:
            configJson = json.load(data_file)
            
        data_file.closed
        
        if self.validateVariable("host_return_policy",configJson,False,-1,conf_file) is False :
            return False
            
        for policy in configJson["host_return_policy"] :
            self.validateVariable("name", policy, True, 0, conf_file)
            if policy["name"] == self.returnPolicyName :
                try:
                    self.billCycle = int(policy["billing_interval"])
                except:
                    Log.logger.error(_('Error in reading value of %s from policy %s. Default lazy policy is used instead') % ("billing_interval",self.returnPolicyName))
                    self.billCycle = 60
                    self.returnWindow = 10
                
                try:
                    self.returnWindow = int(policy["return_interval"])
                except:
                    Log.logger.error(_('Error in reading value of %s from policy %s. Default lazy policy is used instead') % ("return_interval",self.returnPolicyName))
                    self.billCycle = 60
                    self.returnWindow = 10
                
                if self.returnWindow > self.billCycle :  
                    Log.logger.error(_('Return interval in policy %s cannot be bigger than billing interval. Default lazy policy is used instead') % (self.returnPolicyName))
                    self.billCycle = 60
                    self.returnWindow = 10
                return True
        return False

    """
    Check of host reaches the end of a billing cycle
    """
    def checkLazyReturn(self, hostname, launchInSeconds):
        #In case of immediate policy
        if self.billCycle == 0 :
            return True
        
        launchTime = datetime.datetime.utcfromtimestamp(launchInSeconds)
        currentTime = datetime.datetime.utcnow()
        diff = currentTime - launchTime
        remaining = (60 * self.billCycle - diff.seconds) % (60 * self.billCycle)
        if remaining < 180 :
            Log.logger.error(_('Host %s return is being initiated within 3 minutes of expiry and may not be released in time.') % (hostname))
         
        if remaining < 60 * self.returnWindow :
            return True
        return False

    """
    Read deserved slots
    """
    def readDeservedMDS(self, consumerName, resourcePlans):
        result = 0
        #Loop for all resource plans from configuration
        for resPlan in resourcePlans :
            #Run egosh consumer view and get its result
            decoded = ""
            try:
                p = subprocess.Popen(["egosh","consumer","view","-MDS","-P", resPlan,"-l",consumerName],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                output, errors = p.communicate()
                decoded = output.decode('utf-8')
            except:
                Log.logger.error(_('Failed to view MDS resource plan'))
                return result;
            #Read slot mapping
            policyPoint = decoded.find("SlotMapping")
            if policyPoint < 0 :
                return result
            coresPerSlot = int(float(decoded[policyPoint:].split("\n")[0].split(",")[0].strip().split("=")[1]))                
            #If no slot mapping found, use the default from this script
            if coresPerSlot == 0 :
                coresPerSlot = self.slotToCores
            #Read cpu values
            policyPoint = decoded.find("Quota at Full Demand")
            if policyPoint < 0 :
                return result
            cpus = int(float(decoded[policyPoint:].split("\n")[0].split(",")[0].strip().split("=")[1]))
            #Translate cpu to slots using slot mapping
            result = result + cpus / coresPerSlot
            
        return result

    """
    Read deserved slots
    """
    def readDeserved(self, consumerName , resourceGroups):
        decoded = ""
        result = 0
        try:
            p = subprocess.Popen(["egosh","consumer","view","-l",consumerName],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output, errors = p.communicate()
            decoded = output.decode('utf-8')
        except:
            Log.logger.error(_('Failed to view resource plan'))
            return result;
            
        #Get the array of policies
        policyPoint = decoded.find("Policy:")
        if policyPoint < 0 :
            return result
            
        policyArray = decoded[policyPoint:].split("Policy:")            
        
        #Loop for all policies
        for policySeg in policyArray :
            if len(policySeg) == 0 :
                continue
                
            #exclude Management hosts            
            searchPoint = policySeg.find("ResourceGroupName")
            groupName = policySeg[searchPoint:].split("\n")[0].split(":")[1].strip()
            if not groupName in resourceGroups :
                continue
                
            sharedQuota = self.readField(policySeg,"Share Quota")
            plannedQuota = self.readField(policySeg,"Planned Quota")
            owns = self.readField(policySeg,"Owns")
            if owns < 0 :
                owns = 0
            
            if plannedQuota > sharedQuota :
                result = result + owns + plannedQuota
            else :  
                result = result + owns + sharedQuota
                
        return result
                        
    """
    Check host joining time If it is less than demand gab then return with false 
    """
    def checkJoiningTime(self, hostName, isFound, launchTime):
        timestampHistoryFile = self.hfWorkDir + "/" + requestor_name + "host_history.json"
        out = {'history':{}}
        currentTime = datetime.datetime.utcnow()
        result = True
        lastHourResult = True
 
        if not os.path.isfile(timestampHistoryFile):
            dx = {}
            dx['join_time']  = currentTime.strftime("%Y-%m-%d %H:%M:%S.%f")
            dx['lastseen_time'] = currentTime.strftime("%Y-%m-%d %H:%M:%S.%f")
            out['history'][hostName] = dx
        else :
            try:
                with open(timestampHistoryFile) as temp_file:
                    out = json.load(temp_file)
                temp_file.closed
            except:
                dx = {}
                dx['join_time']  = currentTime.strftime("%Y-%m-%d %H:%M:%S.%f")
                dx['lastseen_time'] = currentTime.strftime("%Y-%m-%d %H:%M:%S.%f")
                out['history'][hostName] = dx

        if hostName in out['history'] :
            t2 = currentTime
            try:
                t2 = datetime.datetime.strptime(out['history'][hostName]['join_time'],"%Y-%m-%d %H:%M:%S.%f")
            except:
                Log.logger.warning(_('Unable to read timestamp %s. %s record is ignored. You can safely ignore this warning.') %(out['history'][hostName]['join_time'],timestampHistoryFile))
                out['history'][hostName]['join_time'] = currentTime.strftime("%Y-%m-%d %H:%M:%S.%f")
                        
            diff = currentTime - t2
            if diff.seconds > 60 * self.ego_host_startup_time :
                result = False

            diff = currentTime - launchTime
            if diff.seconds > 3600 :
                lastHourResult = False
        else : 
            dx = {}
            dx['join_time']  = currentTime.strftime("%Y-%m-%d %H:%M:%S.%f")
            dx['lastseen_time'] = currentTime.strftime("%Y-%m-%d %H:%M:%S.%f")
            out['history'][hostName] = dx

        if isFound is True :
            out['history'][hostName]['lastseen_time'] = currentTime.strftime("%Y-%m-%d %H:%M:%S.%f")
 
        with open(timestampHistoryFile, 'w') as outfile:
            json.dump(out,outfile, indent = 2)
            
        return result,lastHourResult

    """
    Check host unavailable time If it is less than demand gap then return with false 
    """
    def checkUnavailableTime(self, hostName, launchTime, timeout = 0):
        timestampHistoryFile = self.hfWorkDir + "/" + requestor_name + "host_history.json"
        out = {'history':{}}
        currentTime = datetime.datetime.utcnow()
        result = False
        unavailableTime = launchTime
 
        if os.path.isfile(timestampHistoryFile):
            try:
                with open(timestampHistoryFile) as temp_file:
                    out = json.load(temp_file)
                temp_file.closed
            except:
                out = {'history':{}}

        if hostName in out['history'] :
            try:
                unavailableTime = datetime.datetime.strptime(out['history'][hostName]['lastseen_time'],"%Y-%m-%d %H:%M:%S.%f")
            except:
                Log.logger.warning(_('Unable to read timestamp for host %s. %s record is ignored. You can safely ignore this warning.') %(hostName,timestampHistoryFile))
                        
        diff = currentTime - unavailableTime
        if timeout == 0 :
            timeout = self.unavailable_host_timeout
        if diff.seconds > 60 * self.unavailable_host_timeout :
            result = True
 
        return result


    def deleteHostFromHistory(self, hostName):
        timestampHistoryFile = self.hfWorkDir + "/" + requestor_name + "host_history.json"
        out = {'history':{}}
 
        if not os.path.isfile(timestampHistoryFile):
            return
        else :
            try:
                with open(timestampHistoryFile) as temp_file:
                    out = json.load(temp_file)
                temp_file.closed
            except:
                out = {'history':{}}

        if hostName in out['history'] :
            del out['history'][hostName]
                        
        with open(timestampHistoryFile, 'w') as outfile:
            json.dump(out,outfile, indent = 2)

    """
    Read configuration file and loop through its applications
    """
    def doCalculation(self):
        Log.logger.debug(_('Entering doCalculation()'))
        status = -1 # -1:  All Applications Disabled 0: Not Ready 1:Ready with no load 2:active
        conf_file = self.hfConfDir + requestor_name + "req_config.json"
        if not os.path.isfile(conf_file):
            print(_('Requestor %s config file: %s does not exist') % (requestor_name , conf_file))
            Log.logger.error(_('Requestor %s config file: %s does not exist') % (requestor_name , conf_file))
            sys.exit(1)

        try:
            with open(conf_file) as data_file:
                configJson = json.load(data_file)
            
            data_file.closed
        except:
            print(_('Requestor %s failed to read config file: %s') % (requestor_name , conf_file))
            Log.logger.error(_('Requestor %s failed to read config file: %s') % (requestor_name , conf_file))
            sys.exit(1)
       
        self.DemandFormat = configJson.get("demand_format")
        if self.DemandFormat is None or self.validateVariable("demand_format", configJson, False, 1, conf_file, 3)  is False :
            self.DemandFormat = 3
        elif self.DemandFormat < 1 or self.DemandFormat > 3 :
            Log.logger.warning(_('%s is out of bounds. Default value of %d is used instead') %("demand_format",3))
            self.DemandFormat = 3
        elif self.DemandFormat == 1 :
            Log.logger.debug('Due to selection of demand format 1, provider_name and template_name are also required, otherwise format 3 shall be used')
            if not configJson["provider_name"]:
                Log.logger.warning(_('%s is not valid string') %("provider_name"))
                self.DemandFormat = 3
            elif not configJson["template_name"]:
                Log.logger.warning(_('%s is not valid string') %("template_name"))
                self.DemandFormat = 3
            else:
                self.provName = configJson.get("provider_name") 
                self.templateName = configJson.get("template_name") 

        MAX_APP_LIMIT = configJson.get("maximum_applications_allowed")
        if MAX_APP_LIMIT is None or MAX_APP_LIMIT == 0 :
            MAX_APP_LIMIT = 20
        
        #Check if policy does have configuration and implementation        
        self.scalingPolicyName = configJson.get("scaling_policy")
        if self.scalingPolicyName is None or self.scalingPolicyName == '' :
            Log.logger.error(_('%s is mandatory in %s') %('Scaling policy',conf_file))
            sys.exit(1)
        policyResult = self.readPolicyConfig()
        if self.scalingPolicyName not in implemented_scaling_policies :
            Log.logger.error(_('Scaling policy %s is not implemented') % self.scalingPolicyName)
            sys.exit(1)
        if policyResult is False :
            print(_('Failed to find scaling policy %s') % self.scalingPolicyName)
            Log.logger.error(_('Failed to find scaling policy %s') % self.scalingPolicyName)
            sys.exit(1)

        #Check if return policy does have configuration and implementation
        self.returnPolicyName = configJson.get("host_return_policy")
        policyResult = self.readReturnPolicyConfig()
        if policyResult is False :
            Log.logger.error(_('Failed to find return policy %s. Default lazy policy is used instead.') % self.returnPolicyName)
        if self.returnPolicyName not in implemented_return_policies :
            Log.logger.error(_('Return policy %s is not implemented') % self.returnPolicyName)
            sys.exit(1)
        
        self.validateVariable("slot_mapping", configJson, True, -1, conf_file)
        self.validateVariable("ncores", configJson["slot_mapping"], True, 1, conf_file)
        self.validateVariable("nram", configJson["slot_mapping"], True, 1, conf_file)

        self.slotToCores = int(configJson["slot_mapping"]["ncores"])
        self.slotToRam = int(configJson["slot_mapping"]["nram"])    
        if self.slotToCores <= 0 :
            Log.logger.warning(_('%s is out of bounds. Default value of %d is used instead') %("ncores",1))
            self.slotToCores = 1
        if self.slotToRam <= 0 :
            Log.logger.warning(_('%s is out of bounds. Default value of %d is used instead') %("nram",256))
            self.slotToRam = 1000
        if self.max_cores_per_hour > 0 and self.max_cores_per_hour < self.slotToCores :
            reqPolicyConFigName = requestor_name + 'req_policy_config.json'
            Log.logger.warning(_('The %s parameter in %s cannot be lower than the number of cores per slot. Value of %d is used instead') %("max_cores_per_hour",reqPolicyConFigName,self.slotToCores))
            self.max_cores_per_hour = self.slotToCores

        if self.validateVariable("unavailable_host_timeout", configJson, False, 1, conf_file) is True :
            self.unavailable_host_timeout = int(configJson["unavailable_host_timeout"])
            if self.unavailable_host_timeout < 30 :
                Log.logger.warning(_('%s is out of bounds. Default value of %d minute(s) is used instead') %("unavailable_host_timeout",30))
                self.unavailable_host_timeout = 30
        
        result = 0
        out = {'throughput':{}}
        
        #Get slot resource groups and MDS resource plans. If they are not found, use the default
        resourceGroups = ["ComputeHosts"] 
        if self.validateVariable("resource_groups", configJson, False, 2, conf_file) is True :
            resourceGroups = configJson["resource_groups"]

        resourcePlans = [] 
        if self.validateVariable("resource_plans", configJson, False, 2, conf_file) is True :
            resourcePlans = configJson["resource_plans"]

        #load older records from saved file to the maximum of one hour
        self.validateVariable("cloud_apps", configJson, True, 2, conf_file)
        
        timestampHistoryFile = self.hfWorkDir + "/" + requestor_name + "timestamp_history.json"
        appCounter = 1
        for apps in configJson["cloud_apps"] :
            #Initialize the array for application throughput and their time_stamps
            arr = []            

            #Get the application Name
            if not apps.get('name'):
                Log.logger.warning(_('Invalid application name has been skipped.'))
            applicationName = apps['name']

            #get number of pending tasks from soam
            decoded = ""
            try:
                p = subprocess.Popen(["soamview","app",applicationName,"-l"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                output, errors = p.communicate()
                decoded = output.decode('utf-8')
                if any( s in errors for s in failover_errors) :
                    self.FailoverState = True
                    Log.logger.error(_(errors))
            except:
                Log.logger.error(_('Failed to access cluster.'))
                break;            
            
            timestampFailoverFile =  self.hfWorkDir + "/" + requestor_name + failtime_temp_file

            if self.FailoverState is False and os.path.isfile(timestampFailoverFile):
                os.remove(timestampFailoverFile)
            
            pendingTasks = self.readField(decoded,"Pending tasks")
            if pendingTasks == -1 : #Failed to parse (Application does not exist)
                continue

            if appCounter >= MAX_APP_LIMIT :
                Log.logger.error(_('Exceeding maximum number of applications.'))
                continue

            try:
                startingPoint = decoded.find("Status")
                if startingPoint < 0 :
                    Log.logger.error(_('Application %s is disabled. Enable the application and try again.')%applicationName)
                    continue
                tempStatus = decoded[startingPoint:].split("\n")[0].split(":")[1].strip().split(" ")[0]
                if tempStatus != "enabled" and tempStatus != "Enabled" :
                    Log.logger.error(_('Application %s is disabled. Enable the application and try again.')%applicationName)
                    continue
            except :
                Log.logger.error(_('Application %s is disabled. Enable the application and try again.')%applicationName)
                continue

            currentPID = 0
            try:
                currentPID = self.readField(decoded,"SSM PID")
            except :
                Log.logger.warning(_('The %s application is enabled but the SSM is not running. Workload information is not available.')%applicationName)
                continue

            if status == -1 :
                status = 0
            
            appCounter = appCounter + 1

            runningTasks = self.readField(decoded,"Running tasks")
            doneTasks = self.readField(decoded,"Done tasks")
            occupied = self.readField(decoded,"Occupied")
            unused = self.readField(decoded,"Unused")
            
            currentSlots = occupied - unused

            #Get the value of deserved slots. If calculation of deserved slots fails, just use the current slots
            deservedSlots = 0
            #First get the conusmer name
            consumerPoint = decoded.find("Consumer")
            if consumerPoint < 0 :
                deservedSlots = currentSlots
            else :
                consumerName = decoded[consumerPoint:].split("\n")[0].split(":")[1].strip()            
                #Then get deserved slots related to the consumer name
                deservedSlots = self.readDeserved(consumerName, resourceGroups)
                deservedSlots += self.readDeservedMDS(consumerName, resourcePlans)
                
            if deservedSlots == 0 :
                deservedSlots = currentSlots
                

            #Save current completed tasks per application
            d1 = {}
            d1['done_tasks'] = doneTasks
            d1['slots'] = currentSlots
            d1['active_tasks'] = pendingTasks + runningTasks
            currentTime = datetime.datetime.now()
            d1['timestamp'] = currentTime.strftime("%Y-%m-%d %H:%M:%S.%f")
            arr.append(d1)

            if not os.path.isfile(timestampHistoryFile):
                dx = {}
                dx['PID']  = currentPID
                dx['records']  = arr
                out['throughput'][applicationName] = dx
                break;            
            
            try:
                with open(timestampHistoryFile) as temp_file:
                    j = json.load(temp_file)
                temp_file.closed
            except:
                dx = {}
                dx['PID']  = currentPID
                dx['records']  = arr
                out['throughput'][applicationName] = dx
                break;            
            
            isReady = False;
            diffTasks = 0
            records = 1 # The current one which we have just red from soamview
            taskRecords = 1
            diffSeconds = 0        

            totalCurrentSlots = currentSlots 
            totalActiveTasks = pendingTasks + runningTasks
            if applicationName in j['throughput'] :
                historyPID = j['throughput'][applicationName]['PID']                
                if historyPID != currentPID :
                    break
                for record in j['throughput'][applicationName]['records'] :
                    t2 = ""
                    try:
                        t2 = datetime.datetime.strptime(record['timestamp'],"%Y-%m-%d %H:%M:%S.%f")
                    except:
                        Log.logger.warning(_('Unable to read timestamp %s. %s record is ignored. You can safely ignore this warning.') %(record['timestamp'],timestampHistoryFile))
                        continue
                        
                    diff = currentTime - t2
                    diffTasks = doneTasks - record['done_tasks']
                    #Stop looking at records that have expired
                    if diff.seconds > 60 * self.history_expiry_time : 
                        diffSeconds = 60 * self.history_expiry_time
                        break
                    # check for warm-up time if not already warmed up
                    if (isReady is False) and (diff.seconds > 60 * self.warmup_time) : # Warmup time is complete
                        isReady = True
                        if status == 0 :
                            status = 1
                     
                    d2 = {}
                    d2['done_tasks'] = record['done_tasks']
                    d2['timestamp'] = record['timestamp']
                    d2['slots'] = record['slots']
                    d2['active_tasks'] = record['active_tasks']
                    arr.append(d2)
                    records = records + 1 #Get the count of records 
                    totalCurrentSlots = totalCurrentSlots + record['slots'] # Collect the number of used slots for all records to get its average 
                    if diff.seconds < 60 * self.active_task_moving_avg : 
                        totalActiveTasks = totalActiveTasks + record['active_tasks']
                        taskRecords = taskRecords + 1
                    diffSeconds = diff.seconds
                    
            #Check if the application has warmed-up time
            if isReady is True :
                Log.logger.debug(_('App:%s Warm up time %d(mins) complete.')%(applicationName, self.warmup_time))

            # Check for additional resources only if there are active tasks and warm-up time is complete
            demandedSlots = 0
            activeTasks = pendingTasks + runningTasks
            # Get average used slots for the time window 
            avgCurrentSlots = (1.0 * totalCurrentSlots / records)
            avgActiveTasks = (1.0 * totalActiveTasks / taskRecords)

            # diffTasks is the number of tasks done in that window ''' 
            Log.logger.debug(_('App:%s active_tasks:%d avg_active_tasks:%.2f done_tasks:%d history_records:%d sum_current_slots:%d')%(applicationName, activeTasks, avgActiveTasks, diffTasks, records, totalCurrentSlots))
            if (avgActiveTasks > 0) and (isReady is True) :
                status = 2
            if (avgActiveTasks > 0) and (isReady is True) and (diffTasks > 0) and (totalCurrentSlots > 0) :
                #throughputPerMinutePerSlot = 1.0 * diffTasks / diffSeconds / avgCurrentSlots
                #Calculating time needed by all deserved slots to finish all the active tasks
                #Average Active tasks are expected to be done in this number of seconds if one slot is being used
                #Expected Finish time in seconds on one slot = average active tasks / rate of tasks finished per second per slot
                expectedFinishTime = int(1.0 * avgCurrentSlots * avgActiveTasks * diffSeconds / diffTasks) 
                demandedSlots = expectedFinishTime / (60 * self.threshold)
                if ((expectedFinishTime % (60 * self.threshold)) > 30) or (demandedSlots == 0):
                    demandedSlots = demandedSlots + 1
                # use predicted current slots to correct expectedFinishTime    
                predictedCurrentSlots = deservedSlots
                # if no deserved slots, we think that there are no active tasks
                if ( predictedCurrentSlots <= 0) :
                    predictedCurrentSlots = 1                    
                Log.logger.debug(_('App:%s throughput[tasks/secs]=%d/%d avg_current_slots:%.2f finish_time:%dsecs desired_finish_time=%dsecs active_tasks:%d avg_active_tasks:%.2f demanded_slots:%d deserved_slots:%d')%(applicationName, diffTasks, diffSeconds, avgCurrentSlots, expectedFinishTime/predictedCurrentSlots, (self.threshold *60), activeTasks, avgActiveTasks, demandedSlots, deservedSlots))
                #if activeTasks <= deservedSlots, there's no need to scale up, also check and allow scale down
                if ((activeTasks > deservedSlots) or (deservedSlots > demandedSlots)) :
                    result = result + demandedSlots - deservedSlots
            elif (activeTasks > 0) and (isReady is True) and (deservedSlots == 0) and (diffTasks == 0) : 
                result = result + 1
            else :
                # Calculate number of slots to return when warmup time reached, 
                if isReady is True and doneTasks > 0 and activeTasks == 0 :
                    Log.logger.debug(_('Idle App:%s active_tasks=%d done_tasks:%d deserved_slots:%.2f')%(applicationName, activeTasks, doneTasks, deservedSlots))

            dx = {}
            dx['PID']  = currentPID
            dx['records']  = arr
            out['throughput'][applicationName] = dx
            
        with open(timestampHistoryFile, 'w') as outfile:
            json.dump(out,outfile, indent = 2)
        
        Log.logger.debug(_('Leaving doCalculation() result:%d status:%d')%(result,status))
        return result , status

    """
    Remove old hosts from cluster. To cover the case of hosts being allocated but they are being returned before bing added to cluster
    """
    def removeOldResources(self, newlyRetruned, allocated_hosts):
        currentTime = datetime.datetime.now()
        returnHistoryFile = self.hfWorkDir + "/" + requestor_name + "return_history.json"
        out = {'records':[]}        

        for host in newlyRetruned :
            d1 = {}
            d1['returned'] = host['hostname']
            d1['timestamp'] = currentTime.strftime("%Y-%m-%d %H:%M:%S.%f")
            out['records'].append(d1)

        try:
            with open(returnHistoryFile) as temp_file:
                j = json.load(temp_file)
            temp_file.closed
        except:
            if (len(newlyRetruned) > 0) :
                with open(returnHistoryFile, 'w') as outfile:
                    json.dump(out,outfile, indent = 2)
            return
 
        hostsArray = []
        
        for record in j['records'] :
            t2 = ""
            try:
                t2 = datetime.datetime.strptime(record['timestamp'],"%Y-%m-%d %H:%M:%S.%f")
            except:
                Log.logger.warning(_('Unable to read timestamp %s. %s record is ignored. You can safely ignore this warning.') %(record['timestamp'],returnHistoryFile))
                continue
            diff = currentTime - t2
            #Stop looking at records that have expired
            if diff.seconds > 60 * self.return_history_expiry_time : 
                break
            
            isNewOne = 0    
            for host2 in allocated_hosts :
                if host2['hostname'] == record['returned'] :
                    isNewOne = 1
                    break
            
            if isNewOne == 1 :
                continue

            d2 = {}
            hostsArray.append(record['returned'])
            hostsArray.append(record['returned'].split(".")[0])
            d2['returned'] = record['returned']
            d2['timestamp'] = record['timestamp']
            out['records'].append(d2)

        with open(returnHistoryFile, 'w') as outfile:
            json.dump(out,outfile, indent = 2)
        
        if (len(hostsArray) == 0) : #No returned hosts
            return

        #Check if any of those hosts has joind the cluster after their return request has been sent
        egoshCloseArray = ["egosh","resource","list","-ll"]
        egoshCloseArray.extend(hostsArray)
        p = subprocess.Popen(egoshCloseArray,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()
        decoded = output.decode('utf-8')        
        notFound = errors.find("No resource found")
        hostsToRemove = []
        
        if notFound >= 0 : #No host is there
            return
        else :
            PendingRemoval = filter(bool,decoded.split("\n"))
            if len(PendingRemoval) == 0 :
                return                   
            del PendingRemoval[0]                  
    
            for pendingHost in PendingRemoval :
                hostsToRemove.append(pendingHost.split(',')[0].replace('"',''))

            if (len(hostsToRemove) > 0) :
                Log.logger.debug(_('Unavailable hosts for removal:'))
            for i in range(0, len(hostsToRemove)):
                Log.logger.debug(_('Host:%s(unavail)') % hostsToRemove[i])

            #Contact ego shell to close the selected hosts
            egoshCloseArray = ["egosh","resource","close","-reclaim"]
            egoshCloseArray.extend(hostsToRemove)
            subprocess.Popen(egoshCloseArray,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        
            #Contact ego shell to remove the selected host from cluster
            egoshCloseArray = ["egosh","resource","remove"]
            egoshCloseArray.extend(hostsToRemove)
            subprocess.Popen(egoshCloseArray,stdout=subprocess.PIPE,stderr=subprocess.PIPE)


    """
    Generate demand requests
    """
    def getDemandRequests(self):

        Log.logger.debug(_('Entering getDemandRequests()'))

        #read input json
        if self.jsonType == "-s":
            j = json.loads(self.jsonIn)
        else:
            with open(self.jsonIn) as data_file:
                j = json.load(data_file)

            data_file.closed
        Log.logger.debug(_('Input json: %s')%(json.dumps(j,indent = 2)))

        neededSlots,status = self.doCalculation()
        demandTitle = 'demand_cores_mem' 
        if self.DemandFormat == 3 :
            demandTitle = 'demand_resource' 
        elif self.DemandFormat == 1 :
            demandTitle = 'demand_hosts' 

        if status == -1 :
            Log.logger.info(_('Applications with running workload were not found.'))
            out = {demandTitle:[]}        
            return (0,json.dumps(out, indent = 2))
        elif status == 0 :
            Log.logger.info(_('Warming up. No demand for hosts'))
            out = {demandTitle:[]}        
            return (0,json.dumps(out, indent = 2))
        elif status == 1 :
            Log.logger.debug(_('Warmed up but no load'))
            
        if neededSlots <= 0 :
            Log.logger.debug(_('No additional cores are required'))
            neededSlots = 0
        
        #get all the resources via egosh command    
        p = subprocess.Popen(["egosh","resource","list","-ll"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()
        decoded = output.decode('utf-8')        

        #Check previous request status from HostFactory and subtract pending requests from the current needed slots computed
        #Pending is divided between 
        # - allocated hosts which are not in cluster yet, 
        # - demand requests in progress
        # - demand requests that are pending
        totalCores = 0
        pendingCores = 0
        waitBeforeDemanding = False
        lastHourCheck = False
        AllocatedCoresInLastHour = 0
         
        if j.get("allocated_hosts") :
            for host in j["allocated_hosts"] :
                if not host.get('ncores') or not host.get('ncpus'):
                    continue
                hostCores = int(host['ncores']) * int(host['ncpus'])
                if host['hostname'].split(".")[0] in decoded:
                    startingPoint = decoded.find(host['hostname'])
                    hoststring = decoded[startingPoint:].split("\n")[0]
                    hostCreationTime = host['launchtime']
                    launchTime = datetime.datetime.utcfromtimestamp(hostCreationTime)
                    if hoststring.find('unavail') > 0 or hoststring.find('"-"') > 0 :
                        pendingCores = pendingCores + hostCores
                        waitBeforeDemanding, lastHourCheck = self.checkJoiningTime(host['hostname'], False, launchTime)
                    else :
                        waitBeforeDemanding, lastHourCheck = self.checkJoiningTime(host['hostname'], True, launchTime)
                        if waitBeforeDemanding is True :
                            pendingCores = pendingCores + hostCores
                        else :
                            totalCores = totalCores + hostCores
                    if lastHourCheck is True :
                        AllocatedCoresInLastHour = AllocatedCoresInLastHour + hostCores 
                else :
                    # if the host has not joined the cluster
                    pendingCores = pendingCores + hostCores

        if j.get("demand_requests_inprogress") :
            for host in j["demand_requests_inprogress"] :
                if not host.get('ncores') or not host.get('ncpus') or not host.get('ninstances'):
                    continue
                hostCores = int(host['ncores']) * int(host['ncpus']) * int(host['ninstances'])
                pendingCores = pendingCores + hostCores
        
        if j.get("demand_requests_pending") :
            for hostPending in j["demand_requests_pending"] :
                if not hostPending.get('ncores') or not hostPending.get('ncpus') or not hostPending.get('ninstances'):
                    continue
                pendingCores = pendingCores + int(hostPending['ncores']) * int(hostPending['ncpus']) * int(hostPending['ninstances'])

        Log.logger.debug(_('Additional slots required: %d, currently provisioning slots: %d, cores allocated in the last hour: %d') % (neededSlots, pendingCores/self.slotToCores, AllocatedCoresInLastHour))
        if pendingCores > 0 :
            neededSlots = neededSlots - (pendingCores) / self.slotToCores
            if neededSlots < 0 :
                neededSlots = 0

        if neededSlots > 0 :
            if self.max_cores_per_hour > 0 :
                slotsRoom = (self.max_cores_per_hour - pendingCores - AllocatedCoresInLastHour)/self.slotToCores
                if slotsRoom <= 0 :
                    neededSlots = 0
                elif slotsRoom < neededSlots :
                    neededSlots = slotsRoom
        
        out = {demandTitle:[]}        
        
        dx = {}
        if neededSlots > 0 :
            if self.DemandFormat == 3 :
                dx['nunits'] = neededSlots
                unit_minimum = {}
                unit_minimum['ncores'] = self.slotToCores
                unit_minimum['nram'] = self.slotToRam
                dx['unit_minimum'] = unit_minimum
            elif self.DemandFormat == 1 :
                dx['ninstances'] = neededSlots
                dx['template_name'] = self.templateName
                dx['prov_name'] = self.provName
            else :
                dx['ncores'] = self.slotToCores * neededSlots
                dx['nram'] = self.slotToRam * neededSlots
            out[demandTitle].append(dx)                
            
        Log.logger.debug(_('Output json: %s')%(json.dumps(out, indent = 2)))
        Log.logger.debug(_('Leaving getDemandRequests()'))
        return (0,json.dumps(out, indent = 2))


    """
    Generate return requests
    """
    def getReturnRequests(self):

        Log.logger.debug(_('Entering getReturnRequests()'))

         #load input json
        if self.jsonType == "-s":
            j = json.loads(self.jsonIn)
        else:
            with open(self.jsonIn) as data_file:
                j = json.load(data_file)

            data_file.closed

        Log.logger.debug(_('Input json: %s')%(json.dumps(j, indent = 2)))
    
        #Read pending hosts first
        pendingRemovalFile = self.hfWorkDir + "/" + requestor_name + "pending_removal.json"
        try:
            with open(pendingRemovalFile) as temp_file:
                previousPendingJson = json.load(temp_file)
            temp_file.closed

            hostsArray = []
            for previousPending in previousPendingJson['return_hosts']:
                hostsArray.append(previousPending)
        except:
            hostsArray = []
        
        #Check if there are new hosts to be returned, 
        # if there are then go to egosh commands directly to remove any pending host
        removedSlots,status = self.doCalculation()
        if self.FailoverState is True :
            timestampFailoverFile =  self.hfWorkDir + "/" + requestor_name + failtime_temp_file
            currentTime = datetime.datetime.utcnow()
            failoverTime = currentTime
            isFailoverTimeout = False
            if os.path.isfile(timestampFailoverFile):
                with open(timestampFailoverFile) as failoverfile:
                    stampstring = failoverfile.read()
                    failoverTime = datetime.datetime.strptime(stampstring,"%Y-%m-%d %H:%M:%S.%f")
                failoverfile.closed

                diff = currentTime - failoverTime
                #Start the process of removing hosts if failover reaches timeout of 10 minutes
                if diff.seconds > 60 * self.ego_failover_timeout :
                    isFailoverTimeout = True
            else :
                with open(timestampFailoverFile, 'w') as failoveroutfile:
                    failoveroutfile.write(currentTime.strftime("%Y-%m-%d %H:%M:%S.%f"))

            if  isFailoverTimeout is False :
                Log.logger.info(_('Possible failover. If EGO does not recover after failover for more than %d minutes, cloud hosts might be returned to the cloud.')%(self.ego_failover_timeout))
                out = {'return_hosts':[]}
                #self.removeOldResources(out['return_hosts'], j["allocated_hosts"])
                return (0, json.dumps(out))

        if status == 0 :
            Log.logger.info(_('Warming up. No hosts for return'))
            out = {'return_hosts':[]}
            self.removeOldResources(out['return_hosts'], j["allocated_hosts"])
            return (0, json.dumps(out))   
        
        incompleteCycle = False

        if (len(hostsArray) > 0) :
            Log.logger.debug(_('Unavailable hosts for removal:'))
        for i in range(0, len(hostsArray)):
            Log.logger.debug(_('Host:%s(unavail)') % hostsArray[i])

        #status 1: Ready with no load, add all allocated hosts as candidates for removal
        if (status == 1 or status == -1) and len(j["allocated_hosts"]) > 0 :
            for host in j["allocated_hosts"] :
                #For hosts in allocated list, if they are already in pending list, skip it
                if any( host['hostname'] in s for s in hostsArray) :
                    continue
                #If not, then add this host as a candidate for removal. 
                #In case of lazy policy, check if host is reaching the end of its cycle
                if self.checkLazyReturn(host['hostname'],host['launchtime']) :
                    hostsArray.append(host['hostname'])
                else :
                    incompleteCycle = True
                    Log.logger.debug(_('Host %s cannot be released in the middle of billing cycle.') % (host['hostname']))
        else :
            if status == 2 and removedSlots < 0 : 
                removedCores = -1 * removedSlots * self.slotToCores
                
                #Get all allocations from egosh
                p = subprocess.Popen(["egosh","alloc","list","-ll"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                output, errors = p.communicate()
                decoded = output.decode('utf-8')        
                allocationResult = decoded.split("\n")        
                
                #Rearrange hosts according to their allocation in an ascending order
                ascendingList = []
                for host in j["allocated_hosts"] :
                    #First check if this host is already in pending list
                    if any( host['hostname'] in s for s in hostsArray) :
                        continue
                
                    #Read and accumulate all allocations related to this hosts
                    #Create an object with Hostname, allocation and number of cores
                    rx = {}
                    rx['hostname'] = host['hostname']
                    rx['ncores'] = host['ncores']
                    rx['ncpus'] = host['ncpus']
                    rx['launchtime'] = host['launchtime']
                    rx['allocation'] = 0
                    
                    for record in allocationResult :
                        startingPoint = record.find(host['hostname'].split(".")[0])
                        if startingPoint < 0 :
                            continue
                        rx['allocation'] = rx['allocation'] + int(record.split('","')[5])
                        allocationResult.remove(record)
                    
                    #if rx['allocation'] == 0 :
                    #    continue
                    
                    #Loop for the list of removal and add the newly created object to the correct place. 
                    for index in range(len(ascendingList)) :
                        if rx['allocation'] < ascendingList[index]['allocation'] :
                            temp = ascendingList[index]
                            ascendingList[index] = rx
                            rx = temp
                    ascendingList.append(rx)
                
                # dump the ascending list 
                if (len(ascendingList) > 0) :
                    Log.logger.debug(_('Hosts in ascending order of allocation:'))
                for i in range(0, len(ascendingList)) :
                    Log.logger.debug(_('Host:%s allocation:%d') % (ascendingList[i]['hostname'], ascendingList[i]['allocation']))
 
                #Loop the final list of removal to create the return json until no room to remove more cores
                counter = 0
                while removedCores > 0 and len(ascendingList) > counter :
                    if self.checkLazyReturn(ascendingList[counter]['hostname'],ascendingList[counter]['launchtime']) :
                        hostCores = int(ascendingList[counter]['ncores']) * int(ascendingList[counter]['ncpus'])
                        if removedCores >= hostCores : 
                            removedCores = removedCores - hostCores
                            hostsArray.append(ascendingList[counter]['hostname'])
                    else :
                        incompleteCycle = True
                        Log.logger.debug(_('Host %s cannot be released in the middle of billing cycle.') % (ascendingList[counter]['hostname']))
                    counter = counter + 1 
            else :
                # No cores to be returned
                # Just return any allocated host which has reached timeout while it is still unavailble at cluster
                egoshOldArray = ["egosh","resource","list","-ll"]        
                oldP = subprocess.Popen(egoshOldArray,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                output, errors = oldP.communicate()
                decoded2 = output.decode('utf-8')
                oldhostsreturned = 0        
                for oldhost in j["allocated_hosts"] :
                    hname = oldhost['hostname']
                    #First check if this host is already in pending list
                    if any( hname in s for s in hostsArray) :
                        continue
                    
                    notFound = decoded2.find(hname.split(".")[0])
                    if notFound < 0 or decoded2[notFound:].split("\n")[0].find("unavail") > 0 :
                        #Check if host has reached timeout.
                        hostCreationTime = oldhost['launchtime']
                        launchTime = datetime.datetime.utcfromtimestamp(hostCreationTime)
                        isTimeOut = self.checkUnavailableTime(hname,launchTime)
                        if isTimeOut is False :
                            continue
                        #currentTime = datetime.datetime.utcnow()
                        #diff = currentTime - launchTime
                        #if self.unavailable_host_timeout > diff.seconds /60 :
                        #    continue
                        
                        hostsArray.append(hname)
                        oldhostsreturned = 1
                        Log.logger.info(_('Releasing host: %s') % hname)
                
                if oldhostsreturned == 0 :
                    Log.logger.debug(_('No cores to be returned'))
                    removedSlots = 0
        
        out = {'return_hosts':[]}
        if len(hostsArray) == 0 :
            #timestampHistoryFile = self.hfWorkDir + "/" + requestor_name + "timestamp_history.json"
            #if status == 1 and os.path.isfile(timestampHistoryFile)  and incompleteCycle is False :
            #    currentTime = datetime.datetime.now().time()
            #    os.rename(timestampHistoryFile,timestampHistoryFile + "%s" % currentTime )
            #    #os.remove(timestampHistoryFile)
                
            self.removeOldResources(out['return_hosts'],j["allocated_hosts"])
            Log.logger.debug(_('Leaving getReturnRequests()'))
            return (0, json.dumps(out))
        else :
            Log.logger.debug(_('Handling removal'))

        #Create a list of short named hosts to cover the Windows case of only computer name witout domain which appears in egosh resource list
        shortHostsArray = []
        Log.logger.info(_('The following hosts are being removed:'))
        for i in range(0, len(hostsArray)):
            Log.logger.info(_('Hostname: %s') % hostsArray[i])
            shortHostsArray.append(hostsArray[i].split(".")[0])
        
        #Run egosh commands to remove hosts. Add successfully removed host to output json and add other hosts to pending list

        #Contact ego shell to close the selected hosts
        egoshCloseArray = ["egosh","resource","close","-reclaim"]
        egoshCloseArray.extend(hostsArray)
        egoshCloseArray.extend(shortHostsArray)
        p = subprocess.Popen(egoshCloseArray,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()
        Log.logger.debug(errors)
        
        #Contact ego shell to remove the selected host from cluster
        egoshCloseArray = ["egosh","resource","remove"]
        egoshCloseArray.extend(hostsArray)
        egoshCloseArray.extend(shortHostsArray)
        p = subprocess.Popen(egoshCloseArray,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()
        Log.logger.debug(errors)
        
        #Contact ego shell to check if host removal is complete and retrieve back the list of unremoved resources
        pendingOut = {'return_hosts':[]}
        egoshCloseArray = ["egosh","resource","list","-ll"]        
        p = subprocess.Popen(egoshCloseArray,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()
        decoded = output.decode('utf-8')        
        for pendingHost in hostsArray :
            notFound = decoded.find(pendingHost)
            if notFound < 0 :
                notFound = decoded.find(pendingHost.split(".")[0])
            
            if notFound >= 0 :
                pendingOut['return_hosts'].append(pendingHost)
            else:
                result = {}
                result['hostname'] = pendingHost
                self.deleteHostFromHistory(pendingHost)
                Log.logger.info(_('Releasing host: %s') % pendingHost)
                out['return_hosts'].append(result)


        #egoshCloseArray = ["egosh","resource","list","-ll"]        
        #egoshCloseArray.extend(hostsArray)
        #p = subprocess.Popen(egoshCloseArray,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        #output, errors = p.communicate()
        #decoded = output.decode('utf-8')        
        #notFound = errors.find("No resource found")
        #if notFound >= 0 : #All hosts can be returned
        #    for pendingHost in hostsArray :
        #        result = {}
        #        result['hostname'] = pendingHost
        #        Log.logger.info(_('Releasing host: %s') % pendingHost)
        #        out['return_hosts'].append(result)
        #else :
        #    PendingRemoval = filter(bool,decoded.split("\n"))                   
        #    decoded2 = errors.decode('utf-8')        
        #    confirmedRemoval = filter(bool,decoded2.split("\n"))
        #    del PendingRemoval[0]                  
        # 
        #    #Save request status to check for it in future calls
        #    for pendingHost in confirmedRemoval :
        #        notFound = pendingHost.find("not found")
        #        if notFound > 0 :                
        #            result = {}
        #            result['hostname'] = pendingHost.replace("Resource <","").replace("> is not found","")
        #            Log.logger.info(_('Releasing host: %s') % result['hostname'])
        #            out['return_hosts'].append(result)
        #    for pendingHost in PendingRemoval :
        #        pendingOut['return_hosts'].append(pendingHost.split(',')[0].replace('"',''))

        with open(pendingRemovalFile, 'w') as outfile:
            json.dump(pendingOut,outfile)
        
        self.removeOldResources(out['return_hosts'],j["allocated_hosts"])

        Log.logger.debug(_('Output json: %s')%(json.dumps(out, indent = 2)))
        Log.logger.debug(_('Leaving getReturnRequests()'))
        return (0, json.dumps(out, indent = 2))

"""
Main
"""
if __name__ == '__main__':
    obj = main(sys.argv[1:])
    if obj.opt_getDemandRequests:
        (retcode, retVal) = obj.getDemandRequests()
        print (retVal)
        sys.exit(retcode)
    elif obj.opt_getReturnRequests:
        (retcode, retVal) = obj.getReturnRequests()
        print (retVal)
        sys.exit(retcode)

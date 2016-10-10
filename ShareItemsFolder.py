#-------------------------------------------------------------
# Name:       Share Items in Folder
# Purpose:    Set the sharing of all items in a folder in ArcGIS Online or Portal. 
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    12/09/2016
# Last Updated:    12/09/2016
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   ArcMap 10.3+
# Python Version:   2.7
#--------------------------------

# Import main modules
import os
import sys
import logging
import smtplib

# Set global variables
# Logging
enableLogging = "false" # Use within code - logger.info("Example..."), logger.warning("Example..."), logger.error("Example...") and to print messages - printMessage("xxx","info"), printMessage("xxx","warning"), printMessage("xxx","error")
logFile = "" # e.g. os.path.join(os.path.dirname(__file__), "Example.log")
# Email logging
sendErrorEmail = "false"
emailServerName = "" # e.g. smtp.gmail.com
emailServerPort = 0 # e.g. 25
emailTo = ""
emailUser = ""
emailPassword = ""
emailSubject = ""
emailMessage = ""
# Proxy
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
# Output
output = None
# ArcGIS desktop installed
arcgisDesktop = "true"

# If ArcGIS desktop installed
if (arcgisDesktop == "true"):
    # Import extra modules
    import arcpy
    # Enable data to be overwritten
    arcpy.env.overwriteOutput = True
# Python version check
if sys.version_info[0] >= 3:
    # Python 3.x
    import urllib.request as urllib2
else:
    # Python 2.x
    import urllib2  
import urllib
import ssl
import json
import string


# Start of main function
def mainFunction(portalUrl,portalAdminName,portalAdminPassword,folderName,itemAccess,groupID,tags): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #     
        printMessage("Connecting to Portal - " + portalUrl + "...","info")
        # Generate token for portal
        token = generateToken(portalAdminName, portalAdminPassword, portalUrl)
                                    
        # Get the folder ID for the folder
        folderID = getfolderID(portalUrl,portalAdminName,folderName,token)

        if folderID:
            # Get all the items in the folder and iterate through these
            getItemsFolder(portalUrl,portalAdminName,folderID,itemAccess,groupID,tags,token)
        else:
            printMessage("Folder does not exist in this users content...","error")
            sys.exit()

        # --------------------------------------- End of code --------------------------------------- #
        # If called from gp tool return the arcpy parameter   
        if __name__ == '__main__':
            # Return the output if there is any
            if output:
                # If ArcGIS desktop installed
                if (arcgisDesktop == "true"):
                    arcpy.SetParameterAsText(1, output)
                # ArcGIS desktop not installed
                else:
                    return output 
        # Otherwise return the result          
        else:
            # Return the output if there is any
            if output:
                return output      
        # Logging
        if (enableLogging == "true"):
            # Log end of process
            logger.info("Process ended.")
            # Remove file handler and close log file        
            logMessage.flush()
            logMessage.close()
            logger.handlers = []
    # If arcpy error
    except arcpy.ExecuteError:           
        # Build and show the error message
        errorMessage = arcpy.GetMessages(2)   
        printMessage(errorMessage,"error")           
        # Logging
        if (enableLogging == "true"):
            # Log error          
            logger.error(errorMessage)
            # Log end of process
            logger.info("Process ended.")            
            # Remove file handler and close log file        
            logMessage.flush()
            logMessage.close()
            logger.handlers = []   
        if (sendErrorEmail == "true"):
            # Send email
            sendEmail(errorMessage)
    # If python error
    except Exception as e:
        errorMessage = ""         
        # Build and show the error message
        # If many arguments
        if (e.args):
            for i in range(len(e.args)):        
                if (i == 0):
                    # Python version check
                    if sys.version_info[0] >= 3:
                        # Python 3.x
                        errorMessage = str(e.args[i]).encode('utf-8').decode('utf-8')
                    else:
                        # Python 2.x
                        errorMessage = unicode(e.args[i]).encode('utf-8')
                else:
                    # Python version check
                    if sys.version_info[0] >= 3:
                        # Python 3.x
                        errorMessage = errorMessage + " " + str(e.args[i]).encode('utf-8').decode('utf-8')
                    else:
                        # Python 2.x
                        errorMessage = errorMessage + " " + unicode(e.args[i]).encode('utf-8')
        # Else just one argument
        else:
            errorMessage = e
        printMessage(errorMessage,"error")
        # Logging
        if (enableLogging == "true"):
            # Log error            
            logger.error(errorMessage)
            # Log end of process
            logger.info("Process ended.")            
            # Remove file handler and close log file        
            logMessage.flush()
            logMessage.close()
            logger.handlers = []   
        if (sendErrorEmail == "true"):
            # Send email
            sendEmail(errorMessage)            
# End of main function


# Start of get items folder function
def getItemsFolder(portalUrl,portalAdminName,folderID,itemAccess,groupID,tags,token):
    dict = {}
    dict['f'] = 'json'
    dict['token'] = token    
    # Python version check
    if sys.version_info[0] >= 3:
        # Python 3.x
        # Encode parameters
        params = urllib.parse.urlencode(dict)
    else:
        # Python 2.x
        # Encode parameters
        params = urllib.urlencode(dict)
    params = params.encode('utf-8')

    # POST the request - Check folders
    requestURL = urllib2.Request(portalUrl + "/sharing/rest/content/users/" + portalAdminName + "/" + folderID,params)
    response = urllib2.urlopen(requestURL)
    # Python version check
    if sys.version_info[0] >= 3:
        # Python 3.x
        # Read json response
        responseJSON = json.loads(response.read().decode('utf8'))
    else:
        # Python 2.x
        # Read json response
        responseJSON = json.loads(response.read())   
    # Log results
    if "error" in responseJSON:
        errDict = responseJSON['error']
        message =  "Error Code: %s \n Message: %s" % (errDict['code'],
        errDict['message'])
        printMessage(message,"error")
    else:
        # For each item in the folder
        itemCount = 0
        for item in responseJSON["items"]:
            # Get the tags and push into an array
            share = "true"
            if (len(tags) > 0):
                share = "false"
                if len(item["tags"]) > 0:
                    tagsMatch = string.split(str(tags), ",")
                    tagsItem = string.split(str(item["tags"]), ",")
                else:
                    tagsItem = ""
                # For each tag in the item
                for tagItem in tagsItem:
                    # For tag to match from the config
                    for tagMatch in tagsMatch:
                        # If tag in config is in item
                        if tagMatch in tagItem:
                            share = "true"
            if (share == "true"):               
                # Share the item
                printMessage("Sharing the item: " + item["id"] + " - " + itemAccess + "...","info")
                shareItem(portalUrl,portalAdminName,folderID,item["id"],itemAccess,groupID,token)
            itemCount = itemCount + 1
        if (itemCount == 0):
            printMessage("No items are in the folder...","error")
            sys.exit()
# End of get items folder function


# Start of share item with portal function
def shareItem(portalUrl,portalAdminName,folderID,itemId,itemAccess,groupID,token):
    # Setup parameters for request 
    dict = {}
    dict['f'] = 'json'
    dict['token'] = token
    dict['everyone'] = "false"
    dict['org'] = "false"
    dict['groups'] = ""
    if (itemAccess.lower() == "public"):
        dict['everyone'] = "true"
        dict['org'] = "true"                
    if (itemAccess.lower() == "org"):
        dict['everyone'] = "false"
        dict['org'] = "true"
    if groupID:
        dict['groups'] = groupID
    # Python version check
    if sys.version_info[0] >= 3:
        # Python 3.x
        # Encode parameters
        params = urllib.parse.urlencode(dict)
    else:
        # Python 2.x
        # Encode parameters
        params = urllib.urlencode(dict)
    params = params.encode('utf-8')

    # POST the request - share item
    requestURL = urllib2.Request(portalUrl + "/sharing/rest/content/users/" + portalAdminName + "/" + folderID + "/items/" + itemId + "/share",params)
    response = urllib2.urlopen(requestURL)
    # Python version check
    if sys.version_info[0] >= 3:
        # Python 3.x
        # Read json response
        responseJSON = json.loads(response.read().decode('utf8'))
    else:
        # Python 2.x
        # Read json response
        responseJSON = json.loads(response.read())    

    # Log results
    if "error" in responseJSON:
        errDict = responseJSON['error']
        message =  "Error Code: %s \n Message: %s" % (errDict['code'],
        errDict['message'])
        printMessage(message,"error")
    else:
        return responseJSON["itemId"]
# End of share item with portal function


# Start of get folder ID function
def getfolderID(portalUrl,portalAdminName,folderName,token):
    dict = {}
    dict['f'] = 'json'
    dict['token'] = token    
    # Python version check
    if sys.version_info[0] >= 3:
        # Python 3.x
        # Encode parameters
        params = urllib.parse.urlencode(dict)
    else:
        # Python 2.x
        # Encode parameters
        params = urllib.urlencode(dict)
    params = params.encode('utf-8')

    # POST the request - Check folders
    requestURL = urllib2.Request(portalUrl + "/sharing/rest/content/users/" + portalAdminName,params)
    response = urllib2.urlopen(requestURL)
    # Python version check
    if sys.version_info[0] >= 3:
        # Python 3.x
        # Read json response
        responseJSON = json.loads(response.read().decode('utf8'))
    else:
        # Python 2.x
        # Read json response
        responseJSON = json.loads(response.read())   
    # Log results
    if "error" in responseJSON:
        errDict = responseJSON['error']
        message =  "Error Code: %s \n Message: %s" % (errDict['code'],
        errDict['message'])
        printMessage(message,"error")
    else:
        folderID = ""
        for folder in responseJSON["folders"]:
            if (folder["title"].lower() == folderName.lower()):
                folderID = folder["id"]
        return folderID
# End of get folder ID function


# Start of get token function
def generateToken(username, password, portalUrl):
    # Python version check
    if sys.version_info[0] >= 3:
        # Python 3.x
        # Encode parameters
        parameters = urllib.parse.urlencode({'username' : username,
                        'password' : password,
                        'client' : 'referer',
                        'referer': portalUrl,
                        'expiration': 180,
                        'f' : 'json'})
    else:
        # Python 2.x
        # Encode parameters
        parameters = urllib.urlencode({'username' : username,
                        'password' : password,
                        'client' : 'referer',
                        'referer': portalUrl,
                        'expiration': 180,
                        'f' : 'json'})
    parameters = parameters.encode('utf-8')
    try:
        urllib2.urlopen(portalUrl + '/sharing/rest/generateToken?',parameters)
        response = urllib2.urlopen(portalUrl + '/sharing/rest/generateToken?',parameters) 
    except Exception as e:
        printMessage( 'Unable to open the url %s/sharing/rest/generateToken' % (portalUrl),'error')
        printMessage(e,'error')

    # Python version check
    if sys.version_info[0] >= 3:
        # Python 3.x
        # Read json response
        responseJSON = json.loads(response.read().decode('utf8'))
    else:
        # Python 2.x
        # Read json response
        responseJSON = json.loads(response.read())

    # Log results
    if "error" in responseJSON:
        errDict = responseJSON['error']
        if int(errDict['code'])==498:
            message = 'Token Expired. Getting new token... '
            token = generateToken(username,password, portalUrl)
        else:
            message =  'Error Code: %s \n Message: %s' % (errDict['code'],
            errDict['message'])
            printMessage(message,'error')
    token = responseJSON.get('token')
    return token
# End of get token function


# Start of print message function
def printMessage(message,type):
    # If ArcGIS desktop installed
    if (arcgisDesktop == "true"):
        if (type.lower() == "warning"):
            arcpy.AddWarning(message)
        elif (type.lower() == "error"):
            arcpy.AddError(message)
        else:
            arcpy.AddMessage(message)
    # ArcGIS desktop not installed
    else:
        print(message)
# End of print message function


# Start of set logging function
def setLogging(logFile):
    # Create a logger
    logger = logging.getLogger(os.path.basename(__file__))
    logger.setLevel(logging.DEBUG)
    # Setup log message handler
    logMessage = logging.FileHandler(logFile)
    # Setup the log formatting
    logFormat = logging.Formatter("%(asctime)s: %(levelname)s - %(message)s", "%d/%m/%Y - %H:%M:%S")
    # Add formatter to log message handler
    logMessage.setFormatter(logFormat)
    # Add log message handler to logger
    logger.addHandler(logMessage) 

    return logger, logMessage               
# End of set logging function


# Start of send email function
def sendEmail(message):
    # Send an email
    printMessage("Sending email...","info")
    # Server and port information
    smtpServer = smtplib.SMTP(emailServerName,emailServerPort) 
    smtpServer.ehlo()
    smtpServer.starttls() 
    smtpServer.ehlo
    # Login with sender email address and password
    smtpServer.login(emailUser, emailPassword)
    # Email content
    header = 'To:' + emailTo + '\n' + 'From: ' + emailUser + '\n' + 'Subject:' + emailSubject + '\n'
    body = header + '\n' + emailMessage + '\n' + '\n' + message
    # Send the email and close the connection
    smtpServer.sendmail(emailUser, emailTo, body)    
# End of send email function


# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE, 
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # Test to see if ArcGIS desktop installed
    if ((os.path.basename(sys.executable).lower() == "arcgispro.exe") or (os.path.basename(sys.executable).lower() == "arcmap.exe") or (os.path.basename(sys.executable).lower() == "arccatalog.exe")):
        arcgisDesktop = "true"
        
    # If ArcGIS desktop installed
    if (arcgisDesktop == "true"):
        argv = tuple(arcpy.GetParameterAsText(i)
            for i in range(arcpy.GetArgumentCount()))
    # ArcGIS desktop not installed
    else:
        argv = sys.argv
        # Delete the first argument, which is the script
        del argv[0] 
    # Logging
    if (enableLogging == "true"):
        # Setup logging
        logger, logMessage = setLogging(logFile)
        # Log start of process
        logger.info("Process started.")
    # Setup the use of a proxy for requests
    if (enableProxy == "true"):
        # Setup the proxy
        proxy = urllib2.ProxyHandler({requestProtocol : proxyURL})
        openURL = urllib2.build_opener(proxy)
        # Install the proxy
        urllib2.install_opener(openURL)
    mainFunction(*argv)

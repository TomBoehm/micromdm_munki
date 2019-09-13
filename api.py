#!/usr/bin/python
# -*- coding: utf-8 -*-

print "Content-type: text/html\n"
print "" 

import cgi,cgitb
import requests
import json
import uuid 
import base64
import plistlib
import subprocess
import os



"""
    SETTINGS
"""
hostname='https://example.com/'
apiKey="---the apiKey---"
tokenLoc='/path/to/sToken_for_micromdm.vpptoken'
profileFolder='/path/to/MobileConfigs/'
munkiFolder='/path/to/munkirepo'

TEST_VALUES = {
    "seriennummer": "C0XXXXXXXXXX",
    "appid": "409183694",
    "action": "installApp",
    #"removeProfile" - "installProfile" - "installApp" - "listAllApps"
    "profile": "Dock.mobileconfig",
    # tom.dock.left - Dock.mobileconfig
}

iOS_list=["C1XXXXXXXXXX", "C2XXXXXXXXXX"]

"""
    FUNCTIONS
"""
def getUdidForSerial(serial, hostname, apiKey):
    response = requests.post(
        hostname+"v1/devices",
        headers={'Content-Type': 'application/json',},
        auth=('micromdm', apiKey),
        data=json.dumps({"filter_serial": [serial] })
    )
    return json.loads(response.content)["devices"][0]["udid"]

def getPricing():
    pricing=json.loads(requests.get(vPPServiceConfigSrv["getVPPAssetsSrvUrl"], data=json.dumps({"sToken": sToken})).content)["assets"]
    for aprice in pricing:
        if ( appid == aprice["adamIdStr"] ) :
            return aprice["pricingParam"]

def serialAssociatedToDevice(appid, seriennummer):
    # ist die App schon der Seriennummer zugewiesen?
    try:
        licenses=json.loads(requests.get(vPPServiceConfigSrv["getLicensesSrvUrl"], data=json.dumps({"sToken": sToken,"serialNumber": seriennummer})).content)["licenses"]
        for license in licenses:
            if ( appid == license["adamIdStr"] ) :
                return 1
        return 0
    except:
        return 0

def getNameOfApp(appid) :
    appInfo=requests.get("https://uclient-api.itunes.apple.com/WebObjects/MZStorePlatform.woa/wa/lookup?version=2&id="+appid+"&p=mdm-lockup&caller=MDM&platform=enterprisestore&cc=at&l=de").content
    try:
        return json.loads(appInfo)["results"][appid]["name"]  
    except:
        return ""

def postMdmCommand(data) :
    response = requests.post( hostname+"v1/commands" , headers={ 'Content-Type': 'application/json', }, auth=('micromdm', apiKey), data=data)

def readFile(fileLocation):
    try:
        file = open(fileLocation, "r")
        fileContent= file.read()
        file.close()
        return fileContent
    except Exception, e: 
        print "ERROR: Could not read " + fileLocation
        
def test_valid_request(manifest, package, search_keys) :
    if manifest not in iOS_list:
        this_manifest=plistlib.readPlist( munkiFolder+"/manifests/"+manifest)
        for akey in search_keys:
            if akey in this_manifest:
                if package in this_manifest[akey]:
                    return True
        if 'included_manifests' in this_manifest:
            for a_manifest in this_manifest["included_manifests"]:
                if  test_valid_request(a_manifest, package, search_keys) == True:
                    return True
        return False
    else:
        return True

def readPlist(plist_path):
    try:
        plist = subprocess.check_output( ['openssl', 'smime', '-in', plist_path, '-inform', 'der', '-verify', '-noverify'],stderr=open('/dev/null', 'w'))
        return plistlib.readPlistFromString(plist)
    except: 
        return plistlib.readPlist(plist_path)


"""
    CGI PARSING
"""
cgitb.enable() #for debugging
form = cgi.FieldStorage()

seriennummer = form.getfirst('seriennummer', TEST_VALUES["seriennummer"])
appid = form.getfirst('appid', TEST_VALUES["appid"])
action = form.getfirst('action', TEST_VALUES["action"])
profile = form.getfirst('profile', TEST_VALUES["profile"])

"""
    PREPARE
"""
sToken = readFile(tokenLoc)
# Die korrekten URLs fuer die Aufrufe holen
vPPServiceConfigSrv = json.loads(requests.get('https://vpp.itunes.apple.com/WebObjects/MZFinance.woa/wa/VPPServiceConfigSrv').content)
# Einen context
context = (json.loads(json.loads(requests.get(vPPServiceConfigSrv["clientConfigSrvUrl"], data=json.dumps({"sToken": sToken})).content)["clientContext"])["hostname"])
if context != hostname:
    print 'context neu holen'
    data = json.dumps({"sToken": sToken, "clientContext": "{\"hostname\": \"" + hostname + "\", \"guid\": \"" + str(uuid.uuid4()) + "\"}"})    
    context = requests.get(vPPServiceConfigSrv["clientConfigSrvUrl"], data=data).content

"""
    DIFFERENT ACTIONS
"""
if ( action == "installApp" ) :
    associated = serialAssociatedToDevice(appid, seriennummer)
    myPricing = getPricing()
    # Die App der Seriennummer zuweisen
    if ( associated == 0 ) :
        requests.get(vPPServiceConfigSrv["manageVPPLicensesByAdamIdSrvUrl"], data=json.dumps({"sToken": sToken,"adamIdStr": appid,"pricingParam": myPricing,"associateSerialNumbers": [ seriennummer ] }))
    udid= getUdidForSerial (seriennummer, hostname, apiKey)
    if test_valid_request(seriennummer, getNameOfApp(appid), ['managed_installs','optional_installs']):
        if ( "udid" != "" ) :
            postMdmCommand(json.dumps({"udid": udid, "request_type": "InstallApplication", "itunes_store_id": int(appid) , "options": {"purchase_method": 1}}))
    else:
        print "The App " + getNameOfApp(appid) + " is not allowed for " + seriennummer 

if ( action == "removeApp" ) :
    associated = serialAssociatedToDevice(appid, seriennummer)
    myPricing = getPricing()
    # Die App der Seriennummer wegnehmen
    if ( associated == 1 ) :
        requests.get(vPPServiceConfigSrv["manageVPPLicensesByAdamIdSrvUrl"], data=json.dumps({"sToken": sToken,"adamIdStr": appid,"pricingParam": myPricing,"disassociateSerialNumbers": [ seriennummer ] }))

if ( action == "listAllApps" ) :
    assets=json.loads(requests.get(vPPServiceConfigSrv["getVPPAssetsSrvUrl"], data=json.dumps({"sToken": sToken})).content)["assets"]
    for asset in assets :
        appid = asset["adamIdStr"]
        titel = getNameOfApp(appid)
        print "ID: " + appid + "   Titel: " + titel.encode('ascii', 'ignore').decode('ascii')
    
if ( action == "listApps4Serial" ) :
    licenses=json.loads(requests.get(vPPServiceConfigSrv["getLicensesSrvUrl"], data=json.dumps({"sToken": sToken,"serialNumber": seriennummer})).content)["licenses"]
    for license in licenses:
        appid = license["adamIdStr"]
        titel = getNameOfApp(appid)
        print "ID: " + appid + "   Titel: " + titel
            
if ( action == "installProfile" ) :
    if (test_valid_request(seriennummer, "Profile - "+profile, ['managed_installs','optional_installs'])) or ( profile == "enroll") :
        udid= getUdidForSerial (seriennummer, hostname, apiKey)
        profile = base64.b64encode( readFile(profileFolder + profile + ".mobileconfig" ) )
        postMdmCommand(json.dumps({"request_type": "InstallProfile", "udid": udid, "payload": profile}))
    else:
        print "The Profile " + profile + " is not allowed for " + seriennummer 
        
if ( action == "removeProfile" ) :
    the_profile=readPlist(profileFolder + profile + ".mobileconfig" )
    identifier=the_profile['PayloadIdentifier']
    if test_valid_request(seriennummer, "Profile - "+profile, ['managed_uninstalls','optional_installs']):
        udid= getUdidForSerial (seriennummer, hostname, apiKey)
        postMdmCommand(json.dumps({"request_type": "RemoveProfile", "udid": udid, "identifier": identifier}))
    else:
        print "The Profile " + profile + " can not be removed from " + seriennummer

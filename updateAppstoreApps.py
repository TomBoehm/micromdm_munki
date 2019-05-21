#!/usr/bin/python

import datetime
import requests
import json
import plistlib
import os.path
import urllib

"""
    SETTINGS
"""
munkiFolder='/Volumes/munki'
vpp_apps_location=munkiFolder+"/pkgsinfo/apps/VPP/"
icon_location=munkiFolder+"/icons_/"

MY_APPS = {
    "425264550": "Blackmagic Disk Speed Test",
    "409183694": "Keynote",
    "1037126344": "Apple Configurator 2",
    "409203825": "Numbers",
    "409201541": "Pages",
}

"""
    FUNCTIONS
"""
def preinstall_script(appName,appVersion,appID):
    return """#!/bin/bash
appName='"""+appName+"""'
appVersion='"""+appVersion+"""'
appID="""+appID+"""
seriennummer=$( system_profiler SPHardwareDataType | grep \'Serial Number (system)\' | awk \'{print $NF}\' )
curl "https://munki.ixpert.at/micromdm/api.py?seriennummer=$seriennummer&appid=$appID&action=installApp"
exit 0"""
    
def uninstall_script(appName,appVersion,appID):
    return """"#!/bin/bash
appName='"""+appName+"""'
appVersion='"""+appVersion+"""'
appID="""+appID+"""
rm -R "/Applications/${appName}.app"
seriennummer=$( system_profiler SPHardwareDataType | grep \'Serial Number (system)\' | awk \'{print $NF}\' )
curl "https://munki.ixpert.at/micromdm/api.py?seriennummer=$seriennummer&appid=$appID&action=removeApp"
exit 0"""

def installcheck_script(appName,appVersion,appID):
    return """#!/bin/bash
appName='"""+appName+"""'
appVersion='"""+appVersion+"""'
appID="""+appID+"""
if [ -d "/Applications/${appName}.app" ]; then
    installedVersion=$( defaults read "/Applications/${appName}.app/Contents/Info.plist" CFBundleShortVersionString )
    if [ "$installedVersion" == "$appVersion" ]; then
        exit 1
    fi
fi    
exit 0"""

default_pkginfo={
    'autoremove': False, 
    'unattended_install': True, 
    'uninstallable': True, 
    'unattended_uninstall': True,
    'installer_type': 'nopkg', 
    'minimum_os_version': '10.4.0', 
    'catalogs': ['testing'], 
    'uninstall_method': 'uninstall_script',
    '_metadata': {
        'munki_version': '', 
        'os_version': '', 
        'created_by': 'tom', 
        'creation_date': ''},  
    'name': '', 
    'description': '', 
    'icon_name': '', 
    'category': '', 
    'version': '', 
    'uninstall_script': '', 
    'preinstall_script': '', 
    'installcheck_script': '', 
    }

for appid in MY_APPS:
    appInfo=requests.get("https://uclient-api.itunes.apple.com/WebObjects/MZStorePlatform.woa/wa/lookup?version=2&id="+appid+"&p=mdm-lockup&caller=MDM&platform=enterprisestore&cc=at&l=de").content
    appInfo=json.loads(appInfo)
    appName=appInfo["results"][appid]["name"]  
    appDescription=appInfo["results"][appid]["description"]["standard"]
    appVersion=appInfo["results"][appid]["offers"][0]["version"]["display"]
    # download Icon
    if ( os.path.exists(icon_location+appName+".png") == False ) :
        appUrl=appInfo["results"][appid]["artwork"]["url"].replace("{w}x{h}bb.{f}", "434x0w.png")
        urllib.urlretrieve (appUrl, icon_location+appName+".png")
            
    try:
      myInfo=plistlib.readPlist(vpp_apps_location+appName+".plist")
    except: 
      myInfo=default_pkginfo
      myInfo["name"] = appName
      myInfo["icon_name"] = appName+".png"
      myInfo["description"] = appDescription    
    
    if ( myInfo["version"] != appVersion ):
        myInfo["version"] = appVersion
        myInfo["_metadata"]["creation_date"] = datetime.datetime.now()
        myInfo["uninstall_script"] = uninstall_script(appName,appVersion,appid)
        myInfo["preinstall_script"] = preinstall_script(appName,appVersion,appid)
        myInfo["installcheck_script"] = installcheck_script(appName,appVersion,appid)
        plistlib.writePlist(myInfo,vpp_apps_location+appName+".plist")
    
quit()




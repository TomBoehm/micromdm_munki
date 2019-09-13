#!/usr/bin/python

import datetime
import requests
import json
import plistlib
import os
import urllib
import sys
import subprocess


"""
    SETTINGS
"""
munkiFolder='/Volumes/munki'
profile_location=munkiFolder+"/pkgsinfo/config/micromdm/"
icon_location=munkiFolder+"/icons_/"

mobileconfigs=(sys.argv[1:])
if (mobileconfigs == [] ):
    mobileconfigs=["/Users/tom/Cloud/MicroMDM/MobileConfigs/DesktopPicture.mobileconfig"]

"""
    FUNCTIONS
"""
    
def readPlist(plist_path):
    try:
        plist = subprocess.check_output( ['openssl', 'smime', '-in', plist_path, '-inform', 'der', '-verify', '-noverify'],stderr=open('/dev/null', 'w'))
        return plistlib.readPlistFromString(plist)
    except: 
        return plistlib.readPlist(plist_path)
        
def preinstall_script(profileName,profileVersion,profileIdentifier):
    return """#!/bin/bash
seriennummer=$( system_profiler SPHardwareDataType | grep 'Serial Number (system)' | awk '{print $NF}' )
curl "https://munki.ixpert.at/micromdm/api.py?seriennummer=$seriennummer&amp;profile="""+profileName+"""&amp;action=installProfile"
exit 0"""
    
def uninstall_script(profileName,profileVersion,profileIdentifier):
    return """#!/bin/bash
seriennummer=$( system_profiler SPHardwareDataType | grep 'Serial Number (system)' | awk '{print $NF}' )
curl "https://munki.ixpert.at/micromdm/api.py?seriennummer=$seriennummer&amp;profile="""+profileName+"""&amp;action=removeProfile"
exit 0"""

def installcheck_script(profileName,profileVersion,profileIdentifier):
    return """#!/bin/bash
myProfile='"""+profileIdentifier+"""'
myVersion='"""+profileVersion+"""'
##############################################################################
# profiles Info in TempFile
if [ -f "/tmp/profile.${myProfile}.plist" ]; then
  rm "/tmp/profile.${myProfile}.plist"
fi
anzahl=$( profiles show -output "/tmp/profile.${myProfile}".plist | cut -d " " -f 3 )
anzahl=$(($anzahl-1))
for i in `seq 0 $anzahl`;
do
    dasProfile=$( /usr/libexec/PlistBuddy -c "print _computerlevel:$i:ProfileIdentifier" /tmp/profile.${myProfile}.plist )
    if [ "$myProfile" == "$dasProfile" ]; then
        #echo $dasProfile
        dieVersion=$( /usr/libexec/PlistBuddy -c "print _computerlevel:$i:ProfileDescription" /tmp/profile.${myProfile}.plist )
        #echo $dieVersion
        if [ "$myVersion" != "$dieVersion" ]; then
            echo "Profil $myProfile in falscher Version $dieVersion installiert ... Version $myVersion wird installiert"
            exit 0
        else
            echo "Profil $myProfile ist korrekt in Version $dieVersion installiert :-)"
            exit 1
        fi
    fi
done   
echo "Profil $myProfile ist nicht installiert ... Version $myVersion wird installiert"

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
    'icon_name': 'Prefs.png', 
    'category': 'Policies_Settings', 
    'version': '', 
    'uninstall_script': '', 
    'preinstall_script': '', 
    'installcheck_script': '', 
    }

for aProfile in mobileconfigs:
    print aProfile
    profileName=os.path.splitext(os.path.basename(aProfile))[0]
    the_profile=readPlist(aProfile)
    #print the_profile
    profileVersion=the_profile["PayloadDescription"]
    profileIdentifier=the_profile["PayloadIdentifier"]
    try:
      myInfo=plistlib.readPlist(profile_location+profileName+".plist")
    except: 
        myInfo=default_pkginfo
        myInfo["name"] = "Profile - "+profileName
        myInfo["display_name"] = "Profile - "+profileName
    if ( myInfo["version"] != profileVersion ):
        myInfo["version"] = profileVersion
        myInfo["_metadata"]["creation_date"] = datetime.datetime.now()
    myInfo["uninstall_script"] = uninstall_script(profileName,profileVersion,profileIdentifier)
    myInfo["preinstall_script"] = preinstall_script(profileName,profileVersion,profileIdentifier)
    myInfo["installcheck_script"] = installcheck_script(profileName,profileVersion,profileIdentifier)
    print profile_location+profileName+".plist"
    plistlib.writePlist(myInfo, profile_location+profileName+".plist")
    

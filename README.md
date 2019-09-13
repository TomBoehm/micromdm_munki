# micromdm_munki
 
The process: Trigger micromdm via Munki.

a) The Apps or the Profiles are assigned to a Munki client via nokpg.plists

b) The Client sends a request to the api.py script  
There is no authentication, but we do check if the action is valid 
- only install if it is in managed_installs or optional_installs
- only remove if it is in managed_uninstalls or optional_installs

c) the api.py script tells micromdm to perform the requested action:
  - installApp
  - removeApp
  - installProfile
  - removeProfile

Add Appstore Apps to Munki:  
updateAppstoreApps.py lists all the VPP apps associated to micromdm and adds them to Munki as nopkg  
importProfile.py should be called with a .mobileconfig as argument. If adds the Profile as nopkg.

------
First draft - alpha

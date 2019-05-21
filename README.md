# micromdm_munki

Trigger micromdm via Munki.

a) The App or the Profile are assigned to a Munki client via nokpg.plists

b) The Client sends a request to the api.py script 
There is no authentication, but we do check if the action is OK 
- only install if it is in managed_installs or optional_installs
- only remove if it is in managed_uninstalls or optional_installs

c) then the script tell micromdm to do so

------

First draft - alpha

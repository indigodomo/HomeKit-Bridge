Release Notes
==========

Version 0.0.6 (Alpha 6)
==========
* Removed the callback URL builder from the server device to instead be dynamic on the API call so it can be easily modified if needed in the future - plus it doesn't need to be saved statically anyway
* Added Indigo-to-Homebridge callback whenever an included object has a change so that HomeKit will stay up-to-date so long as the server is running when an object change takes place
* Changed the object indexer so that having one object on multiple servers would be properly indexed
* Added action indexing for monitored objects
* Added function that when the server configuration is saved the plugin will reindex all devices and actions automatically
* Changed Homebridge startup routine so that when starting a server it will no longer sleep to wait for the HB server to start because that means it cannot answer API queries (something that happens when HB starts and it will hang if sleeping), now it will check every second or so until 30 seconds when it will give up and report an error
* Added error trapping to concurrent threading
* Server status will now show "Starting" when attempting to start Homebridge and switch to "Running" when successful
* Server status will now show "Stopping" when attempting to stop Homebridge and switch to "Stopped" when successful
* Updated to the most current NodeJS script, Lightbulb On/Off functioning but callbacks are not
* Fixed bug that when editing an object on the server list it would not change the object type properly, leading to potentially changing the object type incorrectly or filling the list with unwanted objects
* Fixed a few UI inconsistancies

Known Issues
---------------
* Integrated Homebridge server is partially enabled, currently only Lightbulbs are functional and then only for On/Off
* Action integration not fully coded
* Indigo server information is still being collected in the plugin config but is no longer used or needed and should be removed since don't talk to the Indigo API any longer
* The current API is not locked to Localhost but will need to be prior to being publicly released for security purposes
* Currently using a delay when we get a setCharacteristic to make sure the value reports back in the JSON, but this should really be more dynamic and should go into a loop until we get confirmation from the device via Indigo events.  Since this is tricky it's slated for later implementation because the workaround is fine for now. 
* A failed Homebridge start can cause a minor race condition where HB will continuously try to restart itself, the current solution to this if it happens is to remove the serverId folder under ~/.HomeKit-Bridge so that the restarts cannot be processed.  This is fine because the plugin will regenerate that folder automatically when you turn on your server device.  This has been countered by extra safeguards in server startup and plugin shutdown but it's a HB issue that still needs resolved.

Version 0.0.5 (Alpha 5)
==========
* Moved server folder from ~/.HomeKit-Bridge to the Indigo plugin preferences folder on the recommendation of Jay from Indigo
* Fixed possible infinite loop issue where if starting the HB server from the plugin it was not incrementing wait time, meaning you would have to hard-stop the plugin to get it to recover if the HB server didn't start up
* Changed service start and stop to quote the long path to the Indigo prefs due to path complexity
* Added a failsafe on starting HB from the plugin that if it does not start in the allotted time that it will issue an Unload command just to make sure it isn't in memory and still attempting to start
* Added automatic HB server start on plugin startup as long as the server option to auto start is checked - this allows for someone to prevent an auto start by unchecking this box
* Added automatic HB server stop on plugin shutdown regardless of any selection options because the API won't run when the plugin is stopped anyway so why keep the HB server running?
* Saving a server config dialog will now update the address of the server to reflect the HB port and username
* Added regular server process checking so that the running state of the plugin device will reflect the running state of the service every 30-60 seconds (variable to keep CPU costs down)

Version 0.0.4 (Alpha 4)
==========
* Additional changed to fix Lightbulb definition (note,  you will need to edit your lightbulb devices on the server and re-save them so they reference the correct library, you'll get an error if you do not)
* Fixed API issue where if the item was an action it would not resolve properly and cause an error
* Added error check to API deviceList so that if there is any kind of an error on a device it will not be added to the final result, preventing a Homebridge restart race condition

Version 0.0.3 (Alpha 3)
==========
* Fixed ability to add actions to the HomeKit device list
* Changed LightBulb to Lightbulb for better HomeKit compatibility and naming conventions
* Changed RESTful URL output to remove the cmd parameter

Version 0.0.2 (Alpha 2)
==========
* Server can now FILL with devices, this will take the server up to it's 99 object limit
* Added a catch-all for switches to always include an ON characteristic, even if the device doesn't support On/Off because all devices will fall back to a switch if no other type can be determined
* Added LockTargetState as a mapped characteristic on locks, defaulting to the current state for now (and normally it would anyway)
* Removed FILL and NONE from the device and action lists as they proved unnecessary given that you can FILL or cherry pick or simply don't add devices and those options are already satisfied.  Using ALL is an option for future versions but won't be considered for now
* Added delay after receiving a characteristic change on the API so when it reports the JSON back it represents the values after the action, without this it was reporting back instantly and then the JSON represented the values before the command was called


Version 0.0.1
---------------
* Initial Alpha release
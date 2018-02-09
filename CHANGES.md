Release Notes
==========

Version 0.2.0 (Beta 2)
==========
* New device type added: [Motion Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Integration#motion-sensor) (note that auto detection may be wonky because there are SOOOOOO many ways to define a motion sensor in Indigo that's a bit hit and miss)
* New device type added: [Garage Door Opener](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Integration#garagedooropener) (note that this is currently not fully operations, Homebridge problems suspected, watch for future updates)
* Behind the scenes update to the libraries to no longer do any kind of logging for non plugin devices (it often causes confusion when debug logging is enabled), this will also reduce the footprint of the plugin a bit
* Added failsafe on the validate config method to force the device to stash includedActions and includedDevices if by some chance the user didn't add one or the other - this should prevent any startup problems as a result of these being missing (reported by Autolog)
* Fixed bug where state changed may not cause an update to HomeKit if it's a plugin device versus native
* Changed the "HomeKit Bridge Warning Attempting to control '[device]' from HomeKit and we didn't get notified for 1 second after the action was run, this is a bit slow" message so that it only appears if the request takes more the 3 seconds instead
* Removed all Indigo web references from the plugin config as they were copied from HBB just in case we went with the Indigo API for any reason and we didn't so it's not needed
* Added a [Battery Low % field to the plugin config](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/Plugin-Preferences#low-battery-warning-) for devices that have a 'StatusLowBattery' characteristic (such as motion sensors do) so that if the Indigo device has a battery and this characteristic is part of the HomeKit service selected then we know when to flag that as being "low battery" (NOTE: As this is beta there won't be any migration coding added, please at leat go into the plugin prefs and just save so the new values are stored)
* Added [Battery Low detection](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Integration#statuslowbattery) on devices that permit it (both HomeKit and Indigo device must support battery level) so that if it's below the threshold in plugin prefs it will show as an exclamation on HomeKit and when you tap it it will say "Battery Low"
* Added special exception definition for Fibaro FGMS001 sensors since they also have a Tile/Tamper option that if you have that model of sensor it will show the Tilt/Tamper on the icon of the motion sensor

Known Issues
---------------
* Complications spinning up a second server (http://forums.indigodomo.com/viewtopic.php?p=154391#p154391).  BETA TESTERS: PLEASE TEST ADDING MULTIPLE SERVERS.
* Brand new install with brand new server is still not auto starting the server after config close (reported by Autolog, but he was on 0.1.1 and this was fixed in 0.1.2 so it may not be an issue after all, still needs tested to absolutely certain so it was added to the testing issue on Git)
* Possible feedback loop because when I update HomeKit it causes you to send a request to Indigo, which changes the device and that prompts the plugin to then contact you to let you know that the device was updated.  I’ll have to figure out a creative way to work around that.
* Possible minor race condition (it could be attributed to an experimental version of HBB running) but sometimes commands from HomeKit will cause a series of concurrent thread issues over multiple plugins, indicating that Indigo is too busy to answer, this recovers after a few seconds
* Indigo server information is still being collected in the plugin config but is no longer used or needed and should be removed since don't talk to the Indigo API any longer
* The current API is not locked to Localhost but will need to be prior to being publicly released for security purposes
* A failed Homebridge start can cause a minor race condition where HB will continuously try to restart itself, the current solution to this if it happens is to remove the serverId folder under ~/.HomeKit-Bridge so that the restarts cannot be processed.  This is fine because the plugin will regenerate that folder automatically when you turn on your server device.  This has been countered by extra safeguards in server startup and plugin shutdown but it's a HB issue that still needs resolved.
* Changing the port on a running server will result in the plugin reporting that the port is in use when it's only in use by the currently running server (resolve by stopping the server before attempting to manually change any HB settings)
* If saving the server after adding an object the HomeKit name/type may still show on the form but the Device/Action is set to Fill as it should be

Version 0.1.2 (Beta 1)
==========
* Hello, I would like to introduce you to the new Fan device!  And it's cool.  WOOT.
* Fixed issue with Insteon devices not reporting to HomeKit when they have changed
* Fixed issue where server device would not automatically restart when configuration was changed
* Added server delete routine so that if you delete a server it will stop the server and remove the config folder
* Running multiple servers should now work fine but will need beta tested to be certain, only limited alpha testing was performed

Version 0.0.7 (Alpha 7)
==========
* Fixed bug where locks were looking for the wrong value from HomeKit and as a result wouldn't operate properly
* Changed http server to be multi-threaded after it was apparent that non-concurrent web requests will never work under HomeKit
* Changed API so that it now will wait until Indigo completes the action before it returns values, insuring that everything is now real-time except actions, that get a 5 second delay instead since there is no way to know if it completes or not (and we wouldn't want to because it could be a 30 minute run for all we know)
* Both the plugin and NodeJS are proving to be quite stable right now, alpha is complete and closed beta begins

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
* Fixed a few UI inconsistencies

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
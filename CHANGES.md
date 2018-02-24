Release Notes
==========

Version 0.12.04 (Beta 12 Build 4)
==========
* Added ability to use invert on devices utilizing the new onStateToFullBrightness special action - this completes the ability to fully use Doors, Windows and Coverings with a relay device in either native or inverted mode
* Notes below this point were from a wonky Build 3, just leaving them in the release notes so they are not lost when the Release 3 is removed from Git (otherwise once we go public the plugin store will complain that the plist is incorrect)
* Fixed bug in setting characteristic values where converting from boolean to an integer could result in no value if there was not a validValues attribute in the characteristic
* Added special function 'onStateToFullBrightness' designed to allow relay devices to be controlled on HomeKit services that use 0-100 scale (such as brightness).  Directly created to allow Windows and Doors the ability to be used as On/Off switches in order to utilize the device type and icon.
* Added ability for relay devices to act as window coverings (also uses onStateToFullBrightness)

Known Issues
---------------
* FRESH INSTALLATION ISSUE: It seems fairly universal that the first server you add does not work until you restart the plugin (this likely has been resolved in Beta 9, needs tested to be sure)
* Nest thermostats (perhaps others) will appear to hang in HomeKit when changing temperature setpoints because of how the Nest plugin operates, the changes will be implemented but the Indigo UI will show timeout errors
* Need to remove API port from the plugin config and autodetect it instead when building the server configuration
* The current API is not locked to Localhost but will need to be prior to being publicly released for security purposes
* Changing the port on a running server will result in the plugin reporting that the port is in use when it's only in use by the currently running server (resolve by stopping the server before attempting to manually change any HB settings)
* Errors getting smoke detector working as [reported by Different Computers](http://forums.indigodomo.com/viewtopic.php?p=154957#p154957)
* Removing a device from Indigo that is part of a server will cause a bunch of errors when that server starts, need to add better device presense checking in code as well as delete detection

Wish List
---------------
* Dev device wishlist: Camera RTP Stream Management, Lock Management
* Add a feature to read in HBB and Alexa items to build a cache of already used alias names
* Redo complications to be a selectable list of different complications or the ability to not use one at all

Previous Release Notes
==========

Known Issues
---------------
* FRESH INSTALLATION ISSUE: It seems fairly universal that the first server you add does not work until you restart the plugin (this likely has been resolved in Beta 9, needs tested to be sure)
* Nest thermostats (perhaps others) will appear to hang in HomeKit when changing temperature setpoints because of how the Nest plugin operates, the changes will be implemented but the Indigo UI will show timeout errors
* Need to remove API port from the plugin config and autodetect it instead when building the server configuration
* The current API is not locked to Localhost but will need to be prior to being publicly released for security purposes
* Changing the port on a running server will result in the plugin reporting that the port is in use when it's only in use by the currently running server (resolve by stopping the server before attempting to manually change any HB settings)
* Errors getting smoke detector working as [reported by Different Computers](http://forums.indigodomo.com/viewtopic.php?p=154957#p154957)
* Removing a device from Indigo that is part of a server will cause a bunch of errors when that server starts, need to add better device presense checking in code as well as delete detection

Version 0.12.02 (Beta 12 Build 2) - Re-release of Build 1 due to missing library
---------------
* Added the ability to use relay (On/Off) devices for Windows and Doors in case someone wants to use them as sensors instead of motors - it's always been planned that every Indigo device can map to any HomeKit device but that functionality may not be 100% but that hasn't really be widely implemented yet, this is part of that
* Added DSC alarms plugin state "state.open" for use on Contact Sensors
* Changed the order the plugin checks for actions from generic (*) first to specific (plugin data) first, this way if there is a plugin definition that will always take priority of generic definitions
* Moved several issues out of the release notes and created issues on Git for them
* Started background work on new service load method to replace the existing method
* Fixed bug where state changes would not tell HomeKit to update characteristics

Version 0.12.0 (Beta 12 Build 0)
---------------
* Fixed bug where Window Coverings had a readonly state and were not usable via the Home App
* Fixed bug where Windows had a readonly state and were not usable via the Home App
* Fixed bug where Doors had a readonly state and were not usable via the Home App
* Removed "Automatic Server Wizard" from build entirely, it's been a playground and not supposed to be in beta yet

Version 0.11.0 (Beta 11)
---------------
* This marks just about the last nail in the coffin for Homebridge Buddy as all remaining device types supported under that plugin are now available under HomeKit Bridge and a complete migration routine has been added
* New [Move Items Between Servers](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/Plugin-Menu-Utilities#move-items-between-servers) plugin menu utility that allows you to move devices between servers
* New [Migration From Homebridge Buddy](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/Plugin-Menu-Utilities#migrate-from-homebridge-buddy) available under the plugin menu's Advanced Plugin Actions - this will also auto run if no HomeKit Bridge servers are found on startup (i.e., new refugee from HBB)
* New device type added: [Occupancy Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#occupancysensor) - and in case you aren't clear on what one does then [read the Wiki on it](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/FAQ#what-is-the-difference-between-a-motion-sensor-and-an-occupancy-sensor)
* New device type added: [Door](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#door)
* New device type added: [Window](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#windowcovering)
* New device type added: [Window Covering](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#windowcovering)
* Added auto detection of Homebridge Buddy Wrapper and Alias devices so that they will default to whatever they were defined as in HBB
* Added feature that will prevent a server from starting if there are no objects to serve up
* Fixed HomeKit device list in the Server Device so that it appears as sorted
* Fixed bug where Homebridge Buddy devices were being excluded from the device list entirely
* Fixed bug where read-only characteristics, such as sensors, would not update in realtime on changes
* Fixed current temperature readings by hacking Homebridge build to allow wider temperature ranges, now temperature controls will work properly in all ranges
* Fixed target temperature settings by hacking Homebridge build to allow wider temperature settings
* Fixed known issue: Readonly sensor devices not calling back on state change
* Satisfied wish list item: Sort HK type list alphabetically

Version 0.9.9 (Beta 10)
---------------
* New device type added: [Temperature Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#temperaturesensor) - it should be noted that HomeKit temps, for whatever reason, have a max limit of 0 to 100 Celsius, so if it's 16F that translates to -9C and HomeKit will reject it and make it 32 degrees (the default value).  Don't blame me, talk to Apple.  If this ever changes the plugin will already handle it accurately without any further changes.
* Added native support to temperature sensors for WUnderground and WeatherSnoop devices
* Added callback stub catch-all for characteristics that are read-only or not explicitly defined so they will get caught on device changes to send to HomeKit (i.e., humidity changes)
* Fixed huge SNAFU where I commented out a critical line that caused all commands to get the 30 second timeout error and beachball for that 30 seconds.  It's beta folks, B-E-T-A :)
* Fixed bug to report back to HomeKit a success if the device is already in the state requested (i.e., if it's already On and HomeKit asks us to turn it On then return success even though nothing changed on the device) - this should fix most timeout issues
* Rewrite of the Thermostat handling in plugin - note that I am at a disadvantage because I only have a Nest thermostat which has very long delayed reactions to set point changes, this is untested with "normal" thermostats that do not have to hit the cloud to do updates
* Changed format of logs as they were relatively unreadable with how Python interprets tabs in the log
* Removed logging on class instantiation unless a device is attached because several functions need to iterate the classes and that resulted in numerous "Invalid Indigo Object" items being logged
* Cleaned up miscellaneous log messages that were not needed

Version 0.9.0 (Beta 9)
---------------
* New device type added: [Smoke Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#smokesensor)
* New device type added: [Humidity Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#humiditysensor) - Will also use humidity from the WUnderground plugin or thermostats (although if already using either of these you will need to use a different server device since it's now hard-coded to not permit multiples of the same device under one server unless it is a complication)
* New device type added: [Leak Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#leaksensor)
* New device type added: [Light Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#lightsensor)
* New device type added: [Battery Service](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#batteryservice) - yet another HomeKit device that is not yet supported BUT you can open the details and it will show the battery level and charging state, which means you can trigger from this even if the UI says it's not implemented.  This will work with any Indigo device that has a battery state being reported (i.e., motion sensors, etc)
* Added "Unsupported" as a tag to all devices that are not fully HomeKit ready when you drop down the HomeKit device type in the server so you can easily identify what is going to be an issue.  Once HomeKit officially supports those types they will get changed.  I could leave them out completely to avoid possible confusion but they need to stick around so they can be tested as Homebridge gets updated or HomeKit gets updated.
* Device and action lists in the server dialog will no longer show any device or action that is already added via THIS server and optionally ANY server, this to curb any potential problems caused by using the same device in multiple HomeKit maps.  Complications were created for this purpose.
* Changed the behavior of the checkbox "Only show objects that are not being sent to HomeKit" in the server dialog to mean that devices that are part of ANY HomeKit Bridge server will be excluded from the list, ensuring that the list is always unique.  Also changed the dialog so that this is defaulted.
* Changed the shutdown behavior of the plugin so that when it is shut down or restarted it will no longer wait for the servers to stop and instead will "blind stop" them, this because Indigo has a time limit for shutting down and if there are more than a few running servers this can cause Indigo to do a forced shutdown and while that won't hurt anything it's just ugly and will raise questions.  This will also speed up the time needed to shut down or restart the plugin
* Fixed bug where a device may show a battery level exclamation in HomeKit even though there was no valid battery level in Indigo (Indigo sets a no battery device to None, this got interpreted to 0 which falls below any % threshold set)
* Fixed bug in new server creation where it would not automatically determine port, listen port and username if the user doesn't do anything with the new server dialog except click OK to save it, now the save function will validate those critical parameters and create them if needed - this should fix the initial install failures as well as new server device failures
* Fixed minor issue where the invert on/off checkbox might stay checked or check itself when editing a device added prior to that feature being added, causing you to inadvertently invert an item you are editing when you don't want to (couldn't understand why my front door suddenly was opposite of what it should be)
* Fixed minor issue reported by chobo997 (via PM) that adding multiple items resulted in "Exception in plugin.serverButtonAddDeviceOrAction_Object line 2055: invalid literal for int() with base 10: ''", that possibility is now trapped and will pop a message on the screen
* Fixed known issue: Creating additional servers is not incrementing the user name and then not showing up in Homebridge as a result (reported by Autolog http://forums.indigodomo.com/viewtopic.php?p=154501#p154501)
* Fixed known issue: Complications spinning up a second server (http://forums.indigodomo.com/viewtopic.php?p=154391#p154391)
* Fixed known issue: Adding a device that is already on the included server devices to the list a 2nd time will produce unexpected results, this needs to be prohibited unless it's a complication (i.e., adding door lock as a lock and also as a contact sensor confused HomeKit)
* Removed known issue (not seen since beta 1): A failed Homebridge start can cause a minor race condition where HB will continuously try to restart itself, the current solution to this if it happens is to remove the serverId folder under ~/.HomeKit-Bridge so that the restarts cannot be processed.  This is fine because the plugin will regenerate that folder automatically when you turn on your server device.  This has been countered by extra safeguards in server startup and plugin shutdown but it's a HB issue that still needs resolved.


Version 0.8.0 (Beta 8)
---------------
* Changed behavior of Airfoil when using a Lightbulb HomeKit type so that On/Off will connect/disconnect the Airfoil speaker instead of using the Speaker control of Mute/Unmute which was exactly opposite
* Fixed bug on characteristic action execution where the thread debug message indicating it was checking for a status change output to the main console instead of thread debug
* Fixed bug on characteristic action execution where a run action would error out if it had too many attempts, it should log the message rather than error on the message [reported by Jon](http://forums.indigodomo.com/viewtopic.php?p=154874#p154874)
* Fixed bug on devices that use the Invert On/Off option where the display was correct but the commands would work only after timing out since the commands were not also getting reversed properly
* Fixed bug on receiving characteristic changes from HomeKit where the plugin may execute a characteristic change more than once under certain circumstances, possibly reversing the action that was just executed
* Tested Lightbulb not working for Airfoil control [reported by Jon](http://forums.indigodomo.com/viewtopic.php?p=154874#p154874) but it was working (perhaps as result of the other bug fixes)

Version 0.7.0 (Beta 7)
---------------
* New device type added: [Speaker](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#speaker) - customized to work with Airfoil by default if you choose an airfoil speaker from your list.  Unfortunately after going through all the code to get this working it shows up in HomeKit but is "not yet supported" so we'll have to wait for a HomeKit update - but we'll be ready when HomeKit is.  In the meantime the Airfoil control functionality has been added to Lightbulbs so you can use that to Mute (on/off) and control volume (Brightness)
* New device type added: [Microphone](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#microphone) - I thought I would get clever and use the microphone device since the definition is identical (mute, volume) but, alas, this too is not yet supported
* New device type added: [Contact Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#contactsensor) - this is the first device to actively invert the onState of a device, since it's inverted in HomeKit
* Added Airfoil support despite the setbacks of using Speaker or Microphone, Airfoil can be controlled via a Lightbulb device (On/Off is Mute and Brightness is Volume).  Note that there were a few ways to implement mute and I chose to go with connecting and disconnecting the speaker rather than storing and retrieving the last speaker states
* Added failsafe for open port checking in case, for whatever reason, a empty string is sent to the port checker as it caused an error [as reported by Coolcaper](http://forums.indigodomo.com/viewtopic.php?p=154850#p154850)
* Added failsafe for starting the server to make sure pin, port, listenPort and username are all present and populated to prevent any server startup errors on new server creation [as reported by Coolcaper](http://forums.indigodomo.com/viewtopic.php?p=154854#p154854)
* Added invert option to the server configuration - you can read more about it on the [Server Wiki Page](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/Server-Device#including-your-indigo-objects) where it has been updated to explain the new Invert option
* Added invert ability to Indigo devices that have an onState (dimmers, relays, etc), this will only invert the onState if it's part of the calculation
* Overhaul of HomeKit-to-Indigo commands, it will now wait for the success of the command up to 25 seconds before aborting, please keep an eye on the log for "Maximum time exceeded while setting the '' HomeKit characteristic for..." errors in the log to see if this is going to cause any problems, this overhaul was in direct result to slow-to-respond devices such as Multi IO controllers that may need some time before a door closes and engages the input sensor control
* Fixed typo in the device config where when you edit a device it would not properly fill in the HomeKit device type that was saved with the device
* Fixed bug with complication lookups that would cause an error when selecting FILL or the divider line (oh, the things you don't think to test that make you slap your head and say DOH!  This is why its in beta testing)
* Fixed known issue: Garage doors using the Insteon Multi I/O kit don't report back correctly because of the long delay in getting the Input1 to respond
* Fixed known issue: If saving the server after adding an object the HomeKit name/type may still show on the form but the Device/Action is set to Fill as it should be
* Known issue removed due to no reports of it: Possible feedback loop because when I update HomeKit it causes you to send a request to Indigo, which changes the device and that prompts the plugin to then contact you to let you know that the device was updated.  I’ll have to figure out a creative way to work around that.
* Known issue removed as it was another plugin causing this (and not HKB or HBB): Possible minor race condition (it could be attributed to an experimental version of HBB running) but sometimes commands from HomeKit will cause a series of concurrent thread issues over multiple plugins, indicating that Indigo is too busy to answer, this recovers after a few seconds
* Filled wish list item: User requested devices: Door (Open/Close or Contact) Sensor
* Filled wish list item: Dev device wishlist: Speaker

Version 0.6.1 (Beta 6.1)
---------------
* Added check for Nest states if user has a Nest so that there's no error when Nest does it's 40 million state updates a minute...

Version 0.6.0 (Beta 6)
---------------
* Device FIXED: Garage Door - Homebridge is hyper sensitive to read/write access, the targetstate was set as readonly and that caused Homekit to not even attempt to send a change order
* Added new feature: [Complications](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/Complications) - this is experimental and only in use for thermostats at the moment but will come into play with sprinklers too in the near future since each valve is its own device
* Added startup warning box if the user is hiding any Indigo items to let them know that there are hidden items that can be managed from the plugin - this to head off any possible future support headaches about someone who incorrectly hides something or hides it and forgets but then asks why the device isn't showing up on their lists anymore.  Also [updated the Wiki to prevent unneeded support requests](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/FAQ#why-do-i-get-a-hidden-items-warning-when-i-start-homekit-bridge)
* Added object type of "Homebridge Buddy Wrappers", "Homebridge Buddy Aliases" and "Homebridge Buddy Devices" to the hidden objects manager
* Added ability to translate a dimmer or relay to a fan type (i.e., bathroom fan wall switch can be represented as a fan in HomeKit)
* Major overhaul of how the plugin translates everything to HomeKit, now allows for a much wider array of device mappings and to onboard new services and characteristics many times faster
* Added special abilities on outlets that if they support power metering that it will represet if there is a load on the outlet or not (a HomeKit feature) using that data, if there is no power metering ability then it will always represent the on state of the outlet
* Added config option to plugin preferences to set the threshold for when HomeKit will indicate that a battery level is low (i.e., at 20%), this will only be valid on HomeKit devices that support a battery low indicator and Indigo devices that have a battery
* Added config options to enable/disable complications (experimental)
* Removed debugging code from startup that would add a debug message regarding adding a value to an invalid Indigo object, it was NOT an error but running as designed only that it should not be running on startup it is meant to run when discovering devices on a new server
* Fundamental change in passing ID's to Homebridge, instead of the device ID the plugin now passes an encrypted unique key, this allows us to create complications where multiples of the same device can be synchronized to Homebridge with different functions
* Fixed bug where when using the FILL option on devices or actions that it was possible to get the same stash key
* Fixed known issue: Able to add multiples of the same device but that will cause HomeKit to crash if they are on the same server (perhaps even multiples since it all dumps to HomeKit), need to enforce only adding one of any device but also modify HomeKit to allow this under some circumstances like the fan of an included thermostat since they need to be separate devices
* Fixed Homebridge issue: Change UUID creation to allow for multiple same devices
* Fixed Homebridge issue: Garage doors never even make a request to Indigo at all

Version 0.5.0 (Beta 5)
---------------
* Added new combobox action item in the server called "Delete and Exclude" that allows you to not only delete an item from the list but to also exclude it from all future lists (manageable from the menu), this in direct response to [the complaint from Different Computers](http://forums.indigodomo.com/viewtopic.php?p=154621#p154621) regarding his frustrations with the way device inclusion works
* Added new combobox action item in the server called "Delete and Hide" that allows you to not only delete an item from the list but to hide it for the remainder of the time you have the server dialog open, allowing you to re-fill as needed.  The cache will clear once the dialog is cancelled or saved so that the object you hid will be available again
* Added new menu option to [Manage Hidden Objects](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/Hidden-Objects-Management) 

Version 0.4.0 (Beta 4)
---------------
* New device type added: [Thermostat](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#thermostat) 
* Added temperature display configuration option to server dialog for any temperature device, but specifically thermostats
* Fixed Action Group execution issues from HomeKit by making the response instant and then calling back HomeKit after a few seconds to toggle the switch to the off position - making it a true momentary switch
* Expanded the HomeKit service calls to include the reference server ID to allow for the ability to add additional server configuration options that pass through to devices, such as temperature format
* Disabled the automatic server wizard until it can be reimagined in a more optimized way, it had a 50/50 shot of timing out while calculating and that wouldn't make anything easier supporting users.  It'll be back soon.

Version 0.3.0 (Beta 3)
---------------
* Total rewrite of the HomeKit integration library once it became apparent that it was going to be a runaway train once all HomeKit device types were added, this streamlines and makes it much easier to manage
* Added new Automatic Server Wizard that will automatically create servers for ALL devices in Indigo and automatically manage them from that point forward.  This beta is being released a little early to fix a bug so this isn't fully functional in that it won't create servers but you can see how the process is going to work.
* Put API Port back into the plugin prefs as it is required to build the config (reported by FlyingDiver)

Version 0.2.0 (Beta 2)
---------------
* New device type added: [Motion Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#motion-sensor) (note that auto detection may be wonky because there are SOOOOOO many ways to define a motion sensor in Indigo that's a bit hit and miss)
* New device type added: [Garage Door Opener](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#garagedooropener) (note that this is currently not fully operations, Homebridge problems suspected, watch for future updates)
* Behind the scenes update to the libraries to no longer do any kind of logging for non plugin devices (it often causes confusion when debug logging is enabled), this will also reduce the footprint of the plugin a bit
* Added failsafe on the validate config method to force the device to stash includedActions and includedDevices if by some chance the user didn't add one or the other - this should prevent any startup problems as a result of these being missing (reported by Autolog)
* Fixed bug where state changed may not cause an update to HomeKit if it's a plugin device versus native
* Changed the "HomeKit Bridge Warning Attempting to control '[device]' from HomeKit and we didn't get notified for 1 second after the action was run, this is a bit slow" message so that it only appears if the request takes more the 3 seconds instead
* Removed all Indigo web references from the plugin config as they were copied from HBB just in case we went with the Indigo API for any reason and we didn't so it's not needed
* Added a [Battery Low % field to the plugin config](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/Plugin-Preferences#low-battery-warning-) for devices that have a 'StatusLowBattery' characteristic (such as motion sensors do) so that if the Indigo device has a battery and this characteristic is part of the HomeKit service selected then we know when to flag that as being "low battery" (NOTE: As this is beta there won't be any migration coding added, please at leat go into the plugin prefs and just save so the new values are stored)
* Added [Battery Low detection](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#statuslowbattery) on devices that permit it (both HomeKit and Indigo device must support battery level) so that if it's below the threshold in plugin prefs it will show as an exclamation on HomeKit and when you tap it it will say "Battery Low"
* Added special exception definition for Fibaro FGMS001 sensors since they also have a Tile/Tamper option that if you have that model of sensor it will show the Tilt/Tamper on the icon of the motion sensor

Version 0.1.2 (Beta 1)
---------------
* Hello, I would like to introduce you to the new Fan device!  And it's cool.  WOOT.
* Fixed issue with Insteon devices not reporting to HomeKit when they have changed
* Fixed issue where server device would not automatically restart when configuration was changed
* Added server delete routine so that if you delete a server it will stop the server and remove the config folder
* Running multiple servers should now work fine but will need beta tested to be certain, only limited alpha testing was performed

Version 0.0.7 (Alpha 7)
---------------
* Fixed bug where locks were looking for the wrong value from HomeKit and as a result wouldn't operate properly
* Changed http server to be multi-threaded after it was apparent that non-concurrent web requests will never work under HomeKit
* Changed API so that it now will wait until Indigo completes the action before it returns values, insuring that everything is now real-time except actions, that get a 5 second delay instead since there is no way to know if it completes or not (and we wouldn't want to because it could be a 30 minute run for all we know)
* Both the plugin and NodeJS are proving to be quite stable right now, alpha is complete and closed beta begins

Version 0.0.6 (Alpha 6)
---------------
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
---------------
* Moved server folder from ~/.HomeKit-Bridge to the Indigo plugin preferences folder on the recommendation of Jay from Indigo
* Fixed possible infinite loop issue where if starting the HB server from the plugin it was not incrementing wait time, meaning you would have to hard-stop the plugin to get it to recover if the HB server didn't start up
* Changed service start and stop to quote the long path to the Indigo prefs due to path complexity
* Added a failsafe on starting HB from the plugin that if it does not start in the allotted time that it will issue an Unload command just to make sure it isn't in memory and still attempting to start
* Added automatic HB server start on plugin startup as long as the server option to auto start is checked - this allows for someone to prevent an auto start by unchecking this box
* Added automatic HB server stop on plugin shutdown regardless of any selection options because the API won't run when the plugin is stopped anyway so why keep the HB server running?
* Saving a server config dialog will now update the address of the server to reflect the HB port and username
* Added regular server process checking so that the running state of the plugin device will reflect the running state of the service every 30-60 seconds (variable to keep CPU costs down)

Version 0.0.4 (Alpha 4)
---------------
* Additional changed to fix Lightbulb definition (note,  you will need to edit your lightbulb devices on the server and re-save them so they reference the correct library, you'll get an error if you do not)
* Fixed API issue where if the item was an action it would not resolve properly and cause an error
* Added error check to API deviceList so that if there is any kind of an error on a device it will not be added to the final result, preventing a Homebridge restart race condition

Version 0.0.3 (Alpha 3)
---------------
* Fixed ability to add actions to the HomeKit device list
* Changed LightBulb to Lightbulb for better HomeKit compatibility and naming conventions
* Changed RESTful URL output to remove the cmd parameter

Version 0.0.2 (Alpha 2)
---------------
* Server can now FILL with devices, this will take the server up to it's 99 object limit
* Added a catch-all for switches to always include an ON characteristic, even if the device doesn't support On/Off because all devices will fall back to a switch if no other type can be determined
* Added LockTargetState as a mapped characteristic on locks, defaulting to the current state for now (and normally it would anyway)
* Removed FILL and NONE from the device and action lists as they proved unnecessary given that you can FILL or cherry pick or simply don't add devices and those options are already satisfied.  Using ALL is an option for future versions but won't be considered for now
* Added delay after receiving a characteristic change on the API so when it reports the JSON back it represents the values after the action, without this it was reporting back instantly and then the JSON represented the values before the command was called


Version 0.0.1
---------------
* Initial Alpha release
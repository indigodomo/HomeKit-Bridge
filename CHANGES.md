Release Notes
==========

Version 0.17.4 (Beta 17.4)
==========
* Fixed one metric crap-ton of places where non-ascii characters might cause errors (fixes [non-standard ASCII error reported on the forum](http://forums.indigodomo.com/viewtopic.php?p=156853#p156853))

Previous Release Notes
==========

Version 0.17.3 (Beta 17.3)
---------------
* Added unicode conversion to device names for non-plugin device updates to try to trap any odd names that are used for Indigo devices (strange characters) - as [reported on the forums](http://forums.indigodomo.com/viewtopic.php?p=156812#p156812)
* Expanded the ability of invert to cover **any** device with more than one active characteristic using the onState of a device.  Until now it was built exclusively to handle on/off for simple devices like switches, outlets and various sensors, now it can be used for complex devices such as garage door openers that may use onState for multiple characteristics ([Issue #59](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/59))
* [Issue #59](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/59) resolved

Version 0.17.2 (Beta 17.2)
---------------
* Added Indigo Plugin Store update checker, this will check at 10:00am each day and on plugin startup
* Added Indigo Plugin Store update check to the menu
* Moved log notice about building configuration to the debug log rather than the info log
* Improved performance of Hue bulbs both in general operation but specifically for color changes ([Issue #31](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/31)), it involved a little white lie back to HomeKit to make this work but I don't think it'll be an issue.
* Fixed a few issues on the UI that caused the form to get out of alignment
* Fixed a bug when an Indigo value was "None" that it would cause a message in the log about being unable to convert (re-fixed from 0.17.0) - [Issue #55](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/55)
* [Issue #31](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/31) resolved
* [Issue #55](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/55) resolved

Version 0.17.1 (Beta 17.1)
---------------
* Fixed typo for setting heating and cooling setpoints that were causing errors

Version 0.17.0 (Beta 17.0)
---------------
* **NOTE: This release represents that last of the HomeKit device types currently available through Homebridge.  The next few release hopefully I can add generic enough mappings that they are usable by any Indigo device type to varying degrees so that, at the very least, you get a choice of some icons to use.**
* New device type added: [Camera RTP Stream Management](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#camerartpstreammanagement) - Don't get your hopes up, this is just experimental to give me a place to play around with video streaming
* New device type added: [Fan](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#fan) - There really isn't a lot of difference, but this is the original HomeKit fan (fewer capabilities) and is being added for completeness and in case something different is discovered about it
* New device type added: [Air Quality Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#airqualitysensor)
* New device type added: [Heater / Cooler](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#heatercooler)
* New device type added: [Humidifier / Dehumidifier](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#humidifierdehumidifier)
* Added cooling setpoint and heating setpoint options to thermostats but they don't currently seem to do anything, at least on my system
* Added additional error checking to the HomeKit update query to ensure the device or action group being updated still exists in Indigo
* Added test condition if an Indigo value is None (null, nothing, etc) then the plugin will convert that to the most negative value (0.0, 0, False) - [Issue #55](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/55)
* Changed target temperature range from 10 Celsius to 35 Celsius, down from -100 to 100 on thermostats, it's how it was under HB-Indigo and HBB and that's where it's staying now.  From now on I'm not changing any values like this unless there are at least 10 people requesting it, it's a waste of time and energy that's better spent on other aspects of this plugin.
* [Issue #37](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/37) fully resolved!
* [Issue #55](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/55) resolved

Version 0.16.3 (Beta 16.3)
---------------
* [Issue #37](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/37) hopefully resolved now!

Version 0.16.2 (Beta 16.2)
---------------
* Fixed bug in UI that was showing the header and fields for a device addition/edit when not in the device management view ([Issue #50](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/50))
* Fixed bug from 16.1 that broke the ability to set temperatures if you were using Fahrenheit
* [Issue #50](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/50) resolved
* [Issue #37](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/37) resolved (fixed typo that broke Celsius users)

Version 0.16.1 (Beta 16.1)
---------------
* **NOTE: Due to a fundamental change in temp control you will need to edit all of your sensors and thermostats and determine if the new "Temperature value is Fahrenheit" needs to be checks so the plugin knows to convert it to Celsius.  It's possible that when you add a temperature sensor or thermostat to a server that you won't see the checkbox, I believe this is only because it's an existing server, if you add it and there is no checkbox it'll be there when you edit that same item.**
* Added checkbox to UI to indicate if a thermostat or temperature sensor temperature is in Fahrenheit so that it can be properly converted on a device-by-device basis
* Added new Advance Plugin Device Action to Simulate HomeKit on Server.  This is different than the Plugin version that lets you simulate any device in Indigo, this specifically uses the settings for an item on a server, so you can test how a device you have already set up is being reported back to HomeKit rather than just testing a device that has not yet been sent to HomeKit too see what it'll do
* Changed how temperatures are converted, they will no longer rely on the server setting for temperature but rather on a device basis, meaning that the server setting only impacts the thermostats "view temperature as" UI setting ([Issue #37](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/37) and [Issue #33](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/33))
* Fixed bug where "temperature units" UI in HomeKit always read Fahrenheit regardless of the server setting, it was not geting picked up in the plugin properly and now will report back to HomeKit the correct value ([Issue #37](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/37))
* [Issue #37](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/37) resolved
* [Issue #33](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/33) resolved
* [Issue #48](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/48) resolved
* [Issue #49](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/49) resolved

Version 0.16.0 (Beta 16)
---------------
* Total UI overhaul - if something on it isn't working don't blame me, I was trying to implement YOUR design requests :).  As a result, a good portion of the Wiki will need to be scrapped and rewritten to document this new UI.
* Added new Advanced Plugin Actions option to [view the Homebridge log](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/Plugin-Menu-Utilities#show-homebridge-log)
* Added support for DSC Alarm plugin on Motion Sensors, Garage Door Opener, Smoke Sensor, Occupancy Sensor, Lock Mechanism, and Switch
* Added failsafe check to make sure the user didn't cancel a brand new server config dialog, which would result in a port error.  Pretty minor but an error is an error.
* Added new [Advanced Plugin Device action to Rebuild Homebridge Folder](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/Plugin-Menu-Utilities#rebuild-homebridge-folder), this in case a folder becomes corrupt and needs to be removed and rebuilt, this is the current solution for [Issue #46](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/46) but also serves additional utility for diagnostics as well so it ends up being a good solution
* Changed behavior of clicking SAVE while editing a device ([Issue #34](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/34) and [Issue #22](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/22) and [Issue #14](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/14)) so that now it will pop a warning to let the user know that the edit will be lost but they can click save again to continue
* Removed last few areas where the old FILL command was still being added to forms
* Removed automatic HBB upgrade in case that is causing a problem with not popping up the config dialong on fresh installs since it was reported that when HBB is enabled the dialog would not show but when it was disabled it would ([Issue #12](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/12))
* Changed default for api port in saving the configuration in case any other users report a problem with not having the prefs file
* Upgrade will flush out any devices that still reference the FILL command
* Fixed bug in thermostat sensors that weren't honoring conversion from Fahrenheit if the device was a sensor device in Indigo ([Issue #33](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/33))
* [Issue #33](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/33) resolved
* [Issue #12](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/12) possibly resolved
* [Issue #46](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/46) resolved
* [Issue #34](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/34) resolved
* [Issue #22](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/22) resolved
* [Issue #14](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/14) resolved

Version 0.15.1 (Beta 15.1)
---------------
* Added a check system to the server configuration builder to see if there are key fields missing from the plugin prefs.  This is in direct response to two users reporting that their "apiport" was missing ([Issue #12](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/12))
* Added ability for contact sensors, which already natively invert the on state of a device, to utilize the "invert" checkbox so that it can **not** invert it instead, this in direct response to [Issue #32](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/32)
* Added new utility to the Advanced Plugin Options (under the plugin menu) to [Simulate a HomeKit device](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/Plugin-Menu-Utilities#advanced-plugin-actions) to better diagnose what may be going on, this allows you to see what HomeKit will see when your device is sent to it
* Removed all complications implementation from the plugin as it's going to be totally different when implemented than it was in the experimental implementation, yet the experimental settings were still in the plugin and causing confusion
* Changed [Faucet](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#faucet) to be 3rd Party Only since in Home it constantly says "Updating".  You can use [Valve](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#valve) instead if you want that icon and more functionality.  This in direct response to [Issue #38](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/38)
* Fixed bug where the plugin was loading an unneeded library and **might** cause an error if it ran across a plugin that didn't have an info.plist file
* Fixed bug where choosing a device that could not be auto detected (for instance a "custom" plugin device) then it would generate an error about being able to "iteritems".  Now non detectable devices will default to a switch and a warning will show in the log that it could not be figured out.
* [Issue #32](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/32) resolved
* [Issue #38](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/38) resolved

Version 0.15.0 (Beta 15)
---------------
* Added _experimental_ support for LIFX color bulbs (may experience similar issues to Hue where the colors WILL change but may generate timeout issues on the plugin and it may take 30 seconds to change the color)
* Added version control for better upgrade processing
* Added device deletion detection where if any device that is currently linked to a HomeKit Bridge server is removed from Indigo the plugin will detect that it was removed and then remove it from all impacted servers (and restart them if needed)
* Added device reindexing on server device save as new device adds were not being added to the cache after saving the server which was fine 99% of the time but could cause issues in a few non critical areas
* Removed the FILL option from the UI, now the action and device list will only show actions and devices (for now, future changes to this are still possible)
* Fixed slow response time of device changes and, in particular, rapid device changes no longer beachball ([Issue #17](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/17)) was resolved but it may be at the cost that HomeKit won't always know immediately if the action failed)
* Fixed Nest temperature set point issue ([Issue #18](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/18)) as a result of fixing [Issue #17](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/17).  Executing the online action still takes longer but it will respond in less than 30 seconds now and no longer beachball
* Fixed issue where special characters (backslash, quote, single quote, etc) would not work, they now will appear in HomeKit as literally as they are added into Indigo ([Issue #11](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/11))
* Fixed issue of the server complaining of in-use ports when trying to change the ports on a running server, it now will not allow port changes while the server is running so it can validate ports properly ([Issue #4](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/4))
* Fixed issue where moving items between servers (plugin menu option) would cause the source and destination server to restart after each item moved rather than at the end of all items being moved [Issue #25](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/25)
* Fixed issue where deleting a device in Indigo that is attached to a HomeKit Bridge server would cause the server to throw errors when it started up (and could subsequently throw errors while running).  While the solution will cause the server to start, stop and start again this is an acceptable solution given the rarity of this occurrence.  For the most part this fix is a failsafe as device deletion detection was also added in this release that should proactively remove deleted devices from servers ([Issue #26](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/26))
* [Issue #17](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/17) resolved
* [Issue #18](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/18) resolved
* [Issue #11](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/11) resolved
* [Issue #4](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/4) resolved
* [Issue #25](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/25) resolved
* [Issue #26](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues/26) resolved

Version 0.14.1 (Beta 14 Release 1)
---------------
* NOTE: All known issues and wishlist items have been moved to [Git issues](https://github.com/Colorado4Wheeler/HomeKit-Bridge/issues) instead
* Added support for the Hue bulb plugin, if you use the hueBulb device then the plugin will now support the color settings of the bulb.  This is functional but still under construction so expect timeouts when you change colors on the app until I dial that in, but it WILL change - just don't go doing a thousand color changes until it's completed
* Renamed the device from being "HomeKit Bridge Server" to being "HomeKit Accessory Server" to bring it more in line with what it is: a HomeKit Accessory and also in pursuance of keeping the terms as user friendly and universal as possible
* Changed max value of Color Temperature to 15,000
* Changed the description of "Fan Version 2" to simply "Fan" to avoid confusion.  There is a Fan Version 1 but I don't see ever using it since the V2 does everything the V1 did anyway
* Fixed fairly large bug where conversion from an Indigo type of integer or float to a characteristic required value of the opposite (float or integer) was using the wrong value for calculation, meaning the result was always whatever the default for the characteristic was (often zero) - if you had issues with a device not reporting correctly please try it now to see if it resolved your issue
* Fixed minor bug on new server creation where if you do not add any devices you might get an error when saving the server that "key device not found in dict"
* Removed first revision service initializers (code cleanup)

Version 0.14.0 (Beta 14)
---------------
* New device type added: [Irrigation System](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#irrigationsystem) - Note that complications have not yet been coded so you cannot yet tie zone valves to this but you can see the running state of your sprinklers here
* New device type added: [Air Purifier](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#airpurifier)
* New device type added: [Carbon Monoxide Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#carbonmonoxidesensor)
* New device type added: [Doorbell](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#doorbell) - Don't get your hopes up, this is totally experimental and is likely going to need a lot of work and it was added simply as a development tool for now
* New device type added: [Faucet](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#faucet) - Yea, I don't know who has automated faucets either, but HomeKit seems to think people do or will in their dystopian future....  It's essentially a switch so maybe you can use it for a cool icon for something else
* New device type added: [Security System](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#securitysystem) - This has been coded to work with DSC alarms because it seems to be the most widely used on Indigo, more will be added in the future.  I do not have a DSC so this in the blind, let me know if it works!
* New device type added: [Slat](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#slat)
* New device type added: [Valve](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#valve) - Will be used in complications for irrigation systems when that comes around but for now it's just based on on/off states
* Changed "Unsupported" language to only apply if it's unsupported in Apple Home, the non-Apple Home and Eve because testing showed that almost all "Unsupported" devices work in Eve and non-Apple Home, now items that only workin 3rd party apps will be listed as "3rd Party Only"
* Added stricter conformity to characteristic restrictions (left loose during initial testing) to make sure no value can be greater or less than what HomeKit expects
* Fixed bug where float values would not convert to int values on characteristic validation
* Fixed bug in cache rebuilding that would leave deleted devices or servers in the cache and could cause errors when the plugin would try to access them
* Fixed bug when devices attached to the server are updated but reference a deleted server, the system will now make sure the server ID still exists in Indigo [reported by siclark](http://forums.indigodomo.com/viewtopic.php?p=155668#p155668)

Version 0.13.1 (Beta 13 Release 1)
---------------
* New device type added: [Filter Maintenance](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#filtermaintenance) - I was so excited about this until the dreaded "unsupported" came up.  Hopefully one day soon it will work because I even created a special device for this in Device Extensions.  That's OK, the device extensions device is super cool anyway :)
* New device type added: [Carbon Dioxide Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#carbondioxidesensor)
* Added checkbox to the plugin menu Item Mover utility to show HBB devices with a special suffix, allowing the user to begin to redefine hold HBB Wrappers and Aliases that now have native support and are not needed anymore
* Added 3rd party API framework and integration libraries (more on this later as it's not something the beta testers will be testing at this point)
* Fixed bug in Homebridge Buddy / Homebridge-Indigo migration utility (in Advanced Plugin menu option) that migrated Alias devices when it was supposed to use the native device instead, now it will NOT migrate HBB Alias devices since that device is no longer needed with the ability to define alias names up front
* Fixed bug where under certain circumstances a user could save a device that didn't have a defined HomeKit device type
* Fixed bug where removing a server would cause it to stay in the ID array and cause errors any time a device that was a part of that server is updated in Indigo by rebuilding the ID index after each form save
* Fixed bug where removing a device would cause it to stay in the ID array and cause errors


Version 0.13.0 (Beta 13)
---------------
* This marks the next milestone of inviting the next group of beta testers in since the new plugin install issue has been resolved
* Fixed issue with Contact Sensors where they may not get status updates when the device changes Indigo because the sensor is read-only and using a special "invertedOnState" method
* Fixed bug where creating a server without doing anything other than immediately saving and closing it (i.e., not changing anything or adding devices) would cause it to save with empty ports and usernames and then cause error messages
* Fixed new plugin installation bug (and any possible post-install new server startup issues) by moving the folder check routines into the server startup routine
* Fixed bug where if there were no servers the Homebridge Buddy/Homebridge-Indigo migration routine would run and appear succesful, now it will state that neither was found
* FINALLY removed known issue: FRESH INSTALLATION ISSUE: It seems fairly universal that the first server you add does not work until you restart the plugin (this likely has been resolved in Beta 9, needs tested to be sure)

Version 0.12.04 (Beta 12 Build 4)
---------------
* Added ability to use invert on devices utilizing the new onStateToFullBrightness special action - this completes the ability to fully use Doors, Windows and Coverings with a relay device in either native or inverted mode
* Notes below this point were from a wonky Build 3, just leaving them in the release notes so they are not lost when the Release 3 is removed from Git (otherwise once we go public the plugin store will complain that the plist is incorrect)
* Fixed bug in setting characteristic values where converting from boolean to an integer could result in no value if there was not a validValues attribute in the characteristic
* Added special function 'onStateToFullBrightness' designed to allow relay devices to be controlled on HomeKit services that use 0-100 scale (such as brightness).  Directly created to allow Windows and Doors the ability to be used as On/Off switches in order to utilize the device type and icon.
* Added ability for relay devices to act as window coverings (also uses onStateToFullBrightness)

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
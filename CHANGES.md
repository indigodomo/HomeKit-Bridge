Release Notes
==========

Version 0.0.4 (Alpha 4)
==========
* Additional changed to fix Lightbulb definition (note,  you will need to edit your lightbulb devices on the server and re-save them so they reference the correct library, you'll get an error if you do not)
* Fixed API issue where if the item was an action it would not resolve properly and cause an error
* Added error check to API deviceList so that if there is any kind of an error on a device it will not be added to the final result, preventing a Homebridge restart race condition

Known Issues
---------------
* Action integration not fully coded
* Automatic starting and stopping of Homebridge server on plugin restart not yet implemented
* Currently using a delay when we get a setCharacteristic to make sure the value reports back in the JSON, but this should really be more dynamic and should go into a loop until we get confirmation from the device via Indigo events.  Since this is tricky it's slated for later implementation because the workaround is fine for now. 
* A failed Homebridge start can cause a minor race condition where HB will continuously try to restart itself, the current solution to this if it happens is to remove the serverId folder under ~/.HomeKit-Bridge so that the restarts cannot be processed.  This is fine because the plugin will regenerate that folder automatically when you turn on your server device

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
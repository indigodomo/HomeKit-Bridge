Release Notes
==========

Version 0.0.2 (Alpha 2)
==========
* Server can now FILL with devices, this will take the server up to it's 99 object limit
* Added a catch-all for switches to always include an ON characteristic, even if the device doesn't support On/Off because all devices will fall back to a switch if no other type can be determined
* Added LockTargetState as a mapped characteristic on locks, defaulting to the current state for now (and normally it would anyway)
* Removed FILL and NONE from the device and action lists as they proved unnecessary given that you can FILL or cherry pick or simply don't add devices and those options are already satisfied.  Using ALL is an option for future versions but won't be considered for now
* Added delay after receiving a characteristic change on the API so when it reports the JSON back it represents the values after the action, without this it was reporting back instantly and then the JSON represented the values before the command was called

Known Issues
---------------
* Action integration not fully coded
* Automatic starting and stopping of Homebridge server on plugin restart not yet implemented
* Currently using a delay when we get a setCharacteristic to make sure the value reports back in the JSON, but this should really be more dynamic and should go into a loop until we get confirmation from the device via Indigo events.  Since this is tricky it's slated for later implementation because the workaround is fine for now. 

Version 0.0.1
---------------
* Initial Alpha release
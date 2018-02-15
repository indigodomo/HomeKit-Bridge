HomeKit Bridge
==========

A bridge between HomeKit (via Homebridge) and Indigo.  This is a direct replacement for Homebridge Buddy.  Please note this is in BETA.

Supported Native Devices (Meaning Direct From Indigo to HomeKit Integration)
---------------
* Lightbulb (i.e., dimmer)
* Switch (i.e., relay)
* Outlet
* Lock
* Fan (Beta 1)
* Motion Sensor (Beta 2)
* Garage Door Opener (Beta 2, Fixed in Beta 6)
* Action Groups (Beta 1, Finalized in Beta 4)
* Thermostat (Beta 4)

Current BETA Testing Limitations (ALPHA is complete)
---------------

* Only the above HomeKit device types are currently supported, this is by design while things are being worked out with the new Homebridge integration, once that is dialed in more devices will be added until ALL HomeKit devices are supported
* To save your server configuration simply turn your server device ON (this is by design to simplify saving configs, but is not 100% coded for possible pitfalls)
* Multiple servers should work but anything past the first server has not been thoroughly tested yet
* All mapped devices will use DEFAULT mapping and cannot yet be customized, i.e., if you set a device to be a Lock and it is not an Indigo lock then it likely won't work because the states required to map the device won't exist.  The next major test phase will include the ability to modify this behavior.


HomeKit Bridge
==========

A bridge between HomeKit (via Homebridge) and Indigo.  This is a direct replacement for Homebridge Buddy.  Please note this is in BETA.

Supported Native Devices (Meaning Direct From Indigo to HomeKit Integration)
---------------
* Action Groups
* [Battery Service (Unsupported)](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#batteryservice)
* [Contact Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#contactsensor)
* [Fan Version 2](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#fanv2)
* [Garage Door Opener](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#garagedooropener)
* [Humidity Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#humiditysensor)
* [Leak Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#leaksensor)
* [Light Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#lightsensor)
* [Lightbulb](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#lightbulb)
* [Lock Mechanism](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#lockmechanism)
* [Microphone (Unsupported)](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#microphone)
* [Motion Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#motionsensor)
* [Outlet](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#outlet)
* [Smoke Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#smokesensor)
* [Speaker (Unsupported)](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#speaker)
* [Switch](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#switch)
* [Thermostat](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#thermostat)

Current BETA Testing Limitations (ALPHA is complete)
---------------

* Only the above HomeKit device types are currently supported, this is by design while things are being worked out with the new Homebridge integration, once that is dialed in more devices will be added until ALL HomeKit devices are supported
* To save your server configuration simply turn your server device ON (this is by design to simplify saving configs, but is not 100% coded for possible pitfalls)
* Multiple servers should work but anything past the first server has not been thoroughly tested yet
* All mapped devices will use DEFAULT mapping and cannot yet be customized, i.e., if you set a device to be a Lock and it is not an Indigo lock then it likely won't work because the states required to map the device won't exist.  The next major test phase will include the ability to modify this behavior.


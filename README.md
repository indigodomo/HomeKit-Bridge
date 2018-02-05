HomeKit Bridge
==========

A bridge between HomeKit (via Homebridge) and Indigo.  This is a direct replacement for Homebridge Buddy.  Please not this is in ALPHA.


Current ALPHA Testing Limitations
==========

* Only four HomeKit device types are currently supported: Light Bulb, Switch, Outlet and Lock (this is by design while things are being worked out with the new Homebridge integration, once that is dialed in more devices will be added until ALL HomeKit devices are supported)
* Action groups not fully coded, do not add them to your server yet
* To save your server configuration simply turn your server device ON (this is by design to simplify saving configs, but is not 100% coded for possible pitfalls)
* Deleting a server will not stop the service or remove the config folder under ~/.HomeKit-Bridge/[serverid].  Suggest that you turn OFF the server before deleting it so you don't tie up the port.
* Multiple servers should work but anything past the first server has not been thoroughly tested yet
* All mapped devices will use DEFAULT mapping and cannot yet be customized, i.e., if you set a device to be a Lock and it is not an Indigo lock then it likely won't work because the states required to map the device won't exist.  The next major test phase will include the ability to modify this behavior.
* No integration with Homebridge will currently work because the Homebridge integration is being completely rewritten and until that is done there can be no HomeKit devices
* Because of a major rewrite of how devices get included, All or None as those subroutines have not been yet updated - add devices one by one (Fill has been fixed)
* The device address doesn't yet show the ports or user but will
* During ALPHA testing the full Homebridge config will output to the console, this is by design and will be removed by BETA


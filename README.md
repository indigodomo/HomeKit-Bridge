![](https://github.com/Colorado4Wheeler/WikiDocs/blob/master/HomeKit-Bridge/logo.png)

# HomeKit Bridge

This plugin for the [Indigo Domotics](http://www.indigodomo.com/) home automation platform that publishes Indigo devices and action groups to Homebridge so that you can use your Indigo devices and actions in HomeKit and with Siri.

## This Plugin is BETA

This plugin is being released to the public as a BETA plugin, meaning that it has been working and quite stable for some time under a number of systems (there was a closed beta for a month) that anything may happen and changes happen somewhat rapidly.  If you want the most stable releases then wait until the latest version posts to the [Indigo Plugin Store](http://www.indigodomo.com/pluginstore/) or if you want the release earlier then you can download the latest build as they will be put into a pre-release state for at least a few days in case there are stability issues or new bugs that pop up.

## Supported HomeKit Devices

The following list represents all of the HomeKit devices (which is 99% of all of them) that are supported via this plugin.  Their ability to work with your Indigo devices depends on the type of device you are using.  At this point do not plan on custom plugin devices that do not use standard Indigo device types (switches, dimmers, sensors, thermostats, irrigation, fans, etc) to work as very little custom plugin mappings have been built into this plugin.  That being said, many users find that using a wrapper from another plugin, such as Masquerade, has aided them in getting their custom device to work.

* Action Groups
* [Air Purifier](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#airpurifier)
* [Air Quality Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#airqualitysensor)
* [Battery Service (3rd Party Only)](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#batteryservice)
* [Camera RTP Stream Management](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#camerartpstreammanagement)
* [Carbon Dioxide (CO2) Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#carbondioxidesensor)
* [Carbon Monoxide (CO) Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#carbonmonoxidesensor)
* [Contact Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#contactsensor)
* [Door](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#door)
* [Doorbell (Experimental & Unsupported)](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#doorbell)
* [Fan (Original)](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#fan)
* [Fan](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#fanv2)
* [Faucet (3rd Party Only)](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#faucet)
* [Filter Maintenance (3rd Party Only)](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#filtermaintenance)
* [Garage Door Opener](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#garagedooropener)
* [Heater / Cooler](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#heatercooler)
* [Humidifier / Dehumidifier](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#humidifierdehumidifier)
* [Humidity Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#humiditysensor)
* [Irrigation System](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#irrigationsystem)
* [Leak Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#leaksensor)
* [Light Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#lightsensor)
* [Lightbulb](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#lightbulb)
* [Lock Mechanism](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#lockmechanism)
* [Microphone (3rd Party Only)](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#microphone)
* [Motion Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#motionsensor)
* [Occupancy Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#occupancysensor)
* [Outlet](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#outlet)
* [Security System](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#securitysystem)
* [Slat (3rd Party Only)](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#slat)
* [Smoke Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#smokesensor)
* [Speaker (3rd Party Only)](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#speaker)
* [Switch](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#switch)
* [Temperature Sensor](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#temperaturesensor)
* [Thermostat](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#thermostat)
* [Valve](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#valve)
* [Window](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#window)
* [Window Covering](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#windowcovering)

## Known Issues

You should always refer to the Git issues section to see what the outstanding problems are before reporting a new issue.  Reporting issues via Git is the preferred method of making sure your issue gets resolved as it's easy to get lost in the Indigo forums.

The biggest current issue is only for new installations, please read the quick start guide in the Wiki to familiarize yourself with that issue that requests that you disable Homebridge Buddy prior to installing HomeKit Bridge (you can re-enable it after the initial installation).  Since this is a very small audience of people it may not get addressed as it's be very difficult to reproduce the problem.
# homebridge-indigo
[Homebridge](https://github.com/nfarina/homebridge) platform plugin for the [Indigo home automation server](http://indigodomotics.com/)

Supports the following Indigo device types:
* Lights and Switches (dimmable and non-dimmable, represented as HomeKit lightbulbs)
* Outlets (represented as HomeKit lightbulbs)
* Thermostats (represented as HomeKit thermostats)
* Ceiling Fans (represented as HomeKit fans)
* Actions (optional, represented as HomeKit switches)

# Installation

1. Install homebridge using: npm install -g homebridge
2. Install this plugin using: npm install -g homebridge-indigo
3. Update your configuration file. See sampleconfig.json in this repository for a sample. 

More details can be found in this [discussion thread](http://forums.indigodomo.com/viewtopic.php?f=9&t=15008).

# Configuration

Configuration sample:

 ```
    "platforms": [
        {
            "platform": "Indigo",
            "name": "My Indigo Server",
            "protocol": "http",
            "host": "127.0.0.1",
            "port": "8176",
            "path": "",
            "username": "myusername",
            "password": "mypassword",
            "includeActions": true,
            "includeIds": [ "12345", "67890" ],
            "excludeIds": [ "98765", "43210" ],
            "treatAsSwitchIds": [ "13579", "24680" ],
            "treatAsLockIds": [ "112233", "445566" ],
            "treatAsDoorIds": [ "224466", "664422" ],
            "treatAsGarageDoorIds": [ "223344", "556677" ],
            "treatAsMotionSensorIds": [ "336699" ],
            "treatAsContactSensorIds": [ "446688" ],
            "treatAsWindowIds": [ "123123", "456456" ],
            "treatAsWindowCoveringIds": [ "345345", "678678" ],
            "invertOnOffIds": [ "234234", "567567" ],
            "thermostatsInCelsius": false,
            "accessoryNamePrefix": "",
            "listenPort": 8177
        }
    ]
```

Fields: 
* "platform": Must always be "Indigo" (required)
* "name": Can be anything (required)
* "protocol": "http" or "https" (optional, defaults to "http" if not specified)
* "host": Hostname or IP Address of your Indigo web server (required)
* "port": Port number of your Indigo web server (optional, defaults to "8176" if not specified)
* "path": The path to the root of your Indigo web server (optional, defaults to "" if not specified, only needed if you have a proxy in front of your Indigo web server)
* "username": Username to log into Indigo web server, if applicable (optional)
* "password": Password to log into Indigo web server, if applicable (optional)
* "includeActions": If true, creates HomeKit switches for your actions (optional, defaults to false)
* "includeIds": Array of Indigo IDs to include (optional - if provided, only these Indigo IDs will map to HomeKit devices)
* "excludeIds": Array of Indigo IDs to exclude (optional - if provided, these Indigo IDs will not be mapped to HomeKit devices)
* "treatAsSwitchIds": Array of Indigo IDs to treat as switches (instead of lightbulbs) - devices must support on/off to qualify
* "treatAsLockIds": Array of Indigo IDs to treat as locks (instead of lightbulbs) - devices must support on/off to qualify (on = locked)
* "treatAsDoorIds": Array of Indigo IDs to treat as doors (instead of lightbulbs) - devices must support on/off to qualify (on = open)
* "treatAsGarageDoorIds": Array of Indigo IDs to treat as garage door openers (instead of lightbulbs) - devices must support on/off to qualify (on = open)
* "treatAsMotionSensorIds": Array of Indigo IDs to treat as motion sensors - devices must support on/off to qualify (on = triggered)
* "treatAsContactSensorIds": Array of Indigo IDs to treat as contact sensors - devices must support on/off to qualify (on = contact detected)
* "treatAsWindowIds": Array of Indigo IDs to treat as windows (instead of lightbulbs) - devices must support on/off to qualify (on = open)
* "treatAsWindowCoveringIds": Array of Indigo IDs to treat as window coverings (instead of lightbulbs) - devices must support on/off to qualify (on = open)
* "invertOnOffIds": Array of Indigo IDs where on and off are inverted in meaning (e.g. if a lock, on = unlocked and off = locked)
* "thermostatsInCelsius": If true, thermostats in Indigo are reporting temperatures in celsius (optional, defaults to false)
* "accessoryNamePrefix": Prefix all accessory names with this string (optional, useful for testing)
* "listenPort": homebridge-indigo will listen on this port for device state updates from Indigo (requires compatible Indigo plugin) (optional, defaults to not listening)

Note that if you specify both "includeIds" and "excludeIds", then only the IDs that are in
"includeIds" and missing from "excludeIds" will be mapped to HomeKit devices.  Typically,
you would only specify one or the other, not both of these lists.  If you just want to
expose everything, then omit both of these keys from your configuration.

Also note that any Indigo devices or actions that have Remote Display unchecked in Indigo
will NOT be exposed to HomeKit, because Indigo excludes those devices from its RESTful API.

HomeKit limits bridges to 100 devices, so if you have more than 99 Indigo
devices (and action groups, if you're including them), then you will want
to use includeIds or excludeIds to get your list down to under 100.
homebridge-indigo will only include up to the first 99 accessories discovered.

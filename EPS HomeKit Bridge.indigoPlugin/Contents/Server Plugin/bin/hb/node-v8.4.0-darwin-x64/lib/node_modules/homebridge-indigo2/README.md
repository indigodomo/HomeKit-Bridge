# homebridge-indigo2
[Homebridge](https://github.com/nfarina/homebridge) platform plugin for the [Indigo home automation server](http://indigodomotics.com/) running the [HomeKit-Bridge](https://github.com/Colorado4Wheeler/HomeKit-Bridge) Indigo plugin

# Installation

This plugin is designed to be run in an embedded homebridge instance that
is installed as part of the HomeKit-Bridge Indigo plugin.

# Configuration

Configuration is managed by the HomeKit-Bridge Indigo plugin.

Configuration sample:

 ```
    "platforms": [
        {
            "platform": "Indigo2",
            "name": "My Indigo2 Server",
            "protocol": "http",
            "host": "127.0.0.1",
            "port": 8558,
            "serverId": "12345678",
            "accessoryNamePrefix": "",
            "listenPort": 8559
        }
    ]
```

Fields: 
* "platform": Must always be "Indigo2" (required)
* "name": Can be anything (required)
* "protocol": "http" or "https" (optional, defaults to "http" if not specified)
* "host": Hostname or IP Address of your Indigo web server (required)
* "port": Port number of your HomeKit-Bridge RESTful API server (required)
* "serverId": Identifier of the HomeKit-Bridge server instance (required)
* "accessoryNamePrefix": Prefix all accessory names with this string (optional, useful for testing)
* "listenPort": homebridge-indigo2 will listen on this port for device state updates from HomeKit-Bridge (required)

HomeKit limits bridges to 100 devices.
homebridge-indigo2 will only include up to the first 99 accessories discovered.

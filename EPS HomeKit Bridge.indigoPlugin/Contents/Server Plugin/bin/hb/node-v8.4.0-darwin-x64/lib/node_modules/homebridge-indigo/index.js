/*
Indigo platform shim for HomeBridge
Written by Mike Riccio (https://github.com/webdeck/homebridge-indigo)
See http://www.indigodomo.com/ for more info on Indigo
See http://forums.indigodomo.com/viewtopic.php?f=9&t=15008 for installation instructions

Configuration example for your Homebridge config.json:

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

Fields:
    "platform": Must always be "Indigo" (required)
    "name": Can be anything (required)
    "protocol": "http" or "https" (optional, defaults to "http" if not specified)
    "host": Hostname or IP Address of your Indigo web server (required)
    "port": Port number of your Indigo web server (optional, defaults to "8176" if not specified)
    "path": The path to the root of your Indigo web server (optional, defaults to "" if not specified, only needed if you have a proxy in front of your Indigo web server)
    "username": Username to log into Indigo web server, if applicable (optional)
    "password": Password to log into Indigo web server, if applicable (optional)
    "includeActions": If true, creates HomeKit switches for your actions (optional, defaults to false)
    "includeIds": Array of Indigo IDs to include (optional - if provided, only these Indigo IDs will map to HomeKit devices)
    "excludeIds": Array of Indigo IDs to exclude (optional - if provided, these Indigo IDs will not be mapped to HomeKit devices)
    "treatAsSwitchIds": Array of Indigo IDs to treat as switches (instead of lightbulbs) - devices must support on/off to qualify
    "treatAsLockIds": Array of Indigo IDs to treat as locks (instead of lightbulbs) - devices must support on/off to qualify (on = locked)
    "treatAsDoorIds": Array of Indigo IDs to treat as doors (instead of lightbulbs) - devices must support on/off to qualify (on = open)
    "treatAsGarageDoorIds": Array of Indigo IDs to treat as garage door openers (instead of lightbulbs) - devices must support on/off to qualify (on = open)
    "treatAsMotionSensorIds": Array of Indigo IDs to treat as motion sensors - devices must support on/off to qualify (on = triggered)
    "treatAsContactSensorIds": Array of Indigo IDs to treat as contact sensors - devices must support on/off to qualify (on = contact detected)
    "treatAsWindowIds": Array of Indigo IDs to treat as windows (instead of lightbulbs) - devices must support on/off to qualify (on = open)
    "treatAsWindowCoveringIds": Array of Indigo IDs to treat as window coverings (instead of lightbulbs) - devices must support on/off to qualify (on = open)
    "invertOnOffIds": Array of Indigo IDs where on and off are inverted in meaning (e.g. if a lock, on = unlocked and off = locked)
    "thermostatsInCelsius": If true, thermostats in Indigo are reporting temperatures in celsius (optional, defaults to false)
    "accessoryNamePrefix": Prefix all accessory names with this string (optional, useful for testing)
    "listenPort": homebridge-indigo will listen on this port for device state updates from Indigo (requires compatible Indigo plugin) (optional, defaults to not listening)

Note that if you specify both "includeIds" and "excludeIds", then only the IDs that are in
"includeIds" and missing from "excludeIds" will be mapped to HomeKit devices.  Typically,
you would only specify one or the other, not both of these lists.  If you just want to
expose everything, then omit both of these keys from your configuration.

Also note that any Indigo devices or actions that have Remote Display unchecked in Indigo
will NOT be exposed to HomeKit, because Indigo excludes those devices from its RESTful API.
*/

var request = require("request");
var async = require("async");
var express = require("express");
var bodyParser = require('body-parser');
var inherits = require('util').inherits;
var Service, Characteristic, Accessory, uuid;

module.exports = function(homebridge) {
    Service = homebridge.hap.Service;
    Characteristic = homebridge.hap.Characteristic;
    Accessory = homebridge.hap.Accessory;
    uuid = homebridge.hap.uuid;

    fixInheritance(IndigoAccessory, Accessory);
    fixInheritance(IndigoSwitchAccessory, IndigoAccessory);
    fixInheritance(IndigoLockAccessory, IndigoAccessory);
    fixInheritance(IndigoPositionAccessory, IndigoAccessory);
    fixInheritance(IndigoDoorAccessory, IndigoPositionAccessory);
    fixInheritance(IndigoWindowAccessory, IndigoPositionAccessory);
    fixInheritance(IndigoWindowCoveringAccessory, IndigoPositionAccessory);
    fixInheritance(IndigoGarageDoorAccessory, IndigoAccessory);
    fixInheritance(IndigoMotionSensorAccessory, IndigoAccessory);
    fixInheritance(IndigoContactSensorAccessory, IndigoAccessory);
    fixInheritance(IndigoLightAccessory, IndigoAccessory);
    fixInheritance(IndigoFanAccessory, IndigoAccessory);
    fixInheritance(IndigoThermostatAccessory, IndigoAccessory);
    fixInheritance(IndigoActionAccessory, IndigoAccessory);

    homebridge.registerPlatform("homebridge-indigo", "Indigo", IndigoPlatform);
};

// Necessary because Accessory is defined after we have defined all of our classes
function fixInheritance(subclass, superclass) {
    var proto = subclass.prototype;
    inherits(subclass, superclass);
    subclass.prototype.parent = superclass.prototype;
    for (var mn in proto) {
        subclass.prototype[mn] = proto[mn];
    }
}


// Initialize the homebridge platform
// log: the logger
// config: the contents of the platform's section of config.json
function IndigoPlatform(log, config) {
    this.log = log;

    // We use a queue to serialize all the requests to Indigo
    this.requestQueue = async.queue(
        function(options, callback) {
            this.log("Indigo request: %s", options.url);
            request(options, callback);
        }.bind(this)
    );

    this.foundAccessories = [];
    this.accessoryMap = new Map();

    // Parse all the configuration options
    var protocol = "http";
    if (config.protocol) {
        protocol = config.protocol;
    }

    var port = "8176";
    if (config.port) {
        port = config.port;
    }

    this.path = "";
    if (config.path) {
        this.path = config.path;
        // Make sure path doesn't end with a slash
        if (this.path.length > 0 && this.path.charAt(this.path.length -1) == '/') {
            this.path = this.path.substr(0, this.path.length - 1);
        }
        // Make sure path begins with a slash
        if (this.path.length > 0 && this.path.charAt(0) != "/") {
            this.path = "/" + this.path;
        }
        this.log("Path prefix is %s", this.path);
    }

    this.baseURL = protocol + "://" + config.host + ":" + port;
    this.log("Indigo base URL is %s", this.baseURL);

    if (config.username && config.password) {
        this.auth = {
            user: config.username,
            pass: config.password,
            sendImmediately: false
        };
    }

    this.includeActions = config.includeActions;
    this.includeIds = config.includeIds;
    this.excludeIds = config.excludeIds;
    this.treatAsSwitchIds = config.treatAsSwitchIds;
    this.treatAsLockIds = config.treatAsLockIds;
    this.treatAsDoorIds = config.treatAsDoorIds;
    this.treatAsGarageDoorIds = config.treatAsGarageDoorIds;
    this.treatAsMotionSensorIds = config.treatAsMotionSensorIds;
    this.treatAsContactSensorIds = config.treatAsContactSensorIds;
    this.treatAsWindowIds = config.treatAsWindowIds;
    this.treatAsWindowCoveringIds = config.treatAsWindowCoveringIds;
    this.invertOnOffIds = config.invertOnOffIds;
    this.thermostatsInCelsius = config.thermostatsInCelsius;

    if (config.accessoryNamePrefix) {
        this.accessoryNamePrefix = config.accessoryNamePrefix;
    } else {
        this.accessoryNamePrefix = "";
    }

    // Start the accessory update listener, if configured
    if (config.listenPort) {
        this.app = express();
        this.app.use(bodyParser.json());
        this.app.use(bodyParser.urlencoded({ extended: true }));
        this.app.get("/devices/:id", this.updateAccessory.bind(this));
        this.app.post("/devices/:id", this.updateAccessoryFromPost.bind(this));
        this.app.listen(config.listenPort,
            function() {
                this.log("Listening on port %d", config.listenPort);
            }.bind(this)
        );
    }
}

// Invokes callback(accessories[]) with all of the discovered accessories for this platform
IndigoPlatform.prototype.accessories = function(callback) {
    var requestURLs = [ this.path + "/devices.json/" ];
    if (this.includeActions) {
        requestURLs.push(this.path + "/actions.json/");
    }

    async.eachSeries(requestURLs,
        function(requestURL, asyncCallback) {
            this.discoverAccessories(requestURL, asyncCallback);
        }.bind(this),
        function (asyncError) {
            if (asyncError) {
                this.log(asyncError);
            }

            if (this.foundAccessories.length > 99) {
                this.log("*** WARNING *** you have %s accessories.",
                         this.foundAccessories.length);
                this.log("*** Limiting to the first 99 discovered. ***");
                this.log("*** See README.md for how to filter your list. ***");
                this.foundAccessories = this.foundAccessories.slice(0, 99);
            }

            this.log("Created %s accessories", this.foundAccessories.length);
            callback(this.foundAccessories.sort(
                function (a, b) {
                    return (a.name > b.name) - (a.name < b.name);
                }
            ));
        }.bind(this)
    );
};

// Discovers all of the accessories under a root Indigo RESTful API node (e.g. devices, actions, etc.)
// Populates this.foundAccessories and this.accessoryMap
// requestURL: the Indigo RESTful API URL to query
// callback: invokes callback(error) when all accessories have been discovered; error is undefined if no error occurred
IndigoPlatform.prototype.discoverAccessories = function(requestURL, callback) {
    this.indigoRequestJSON(requestURL, "GET", null,
        function(error, json) {
            if (error) {
                callback(error);
            }
            else {
                async.eachSeries(json, this.addAccessory.bind(this),
                    function(asyncError) {
                        if (asyncError) {
                            callback(asyncError);
                        } else {
                            callback();
                        }
                    }
                );
            }
        }.bind(this),
        // jsonFixer: Indigo has a bug that if the first item has remote display
        // disabled, the returned JSON array has an extra comma at the beginning
        function(body) {
            var firstComma = body.indexOf(",");
            if (firstComma > 0 && firstComma < 5) {
                body = body.substr(0, firstComma) + body.substr(firstComma + 1);
            }
            return (body);
        }
    );
};

// Adds an IndigoAccessory object to this.foundAccessories and this.accessoryMap
// item: JSON describing the device, as returned by the root of the Indigo RESTful API (e.g. /devices.json/)
// callback: invokes callback(error), error is always undefined as we want to ignore errors
// Note: does not create and add the IndigoAccessory if it is an unknoen type or is excluded by the config
IndigoPlatform.prototype.addAccessory = function(item, callback) {
    // Get the details of the item, using its provided restURL
    this.indigoRequestJSON(item.restURL, "GET", null,
        function(error, json) {
            if (error) {
                this.log("Ignoring accessory %s due to error", item.restURL);
                callback();
            }
            else {
                // Actions are missing a type field
                if (json.restParent == "actions") {
                    json.type = "Action";
                }
                this.log("Discovered %s (ID %s): %s", json.type, json.id, json.name);
                if (this.includeItemId(json.id)) {
                    var accessory = this.createAccessoryFromJSON(item.restURL, json);
                    if (accessory) {
                        this.foundAccessories.push(accessory);
                        this.accessoryMap.set(String(json.id), accessory);
                    } else {
                        this.log("Ignoring unknown accessory type %s", json.type);
                    }
                }
                else {
                    this.log("Ignoring excluded ID %s", json.id);
                }
                callback();
            }
        }.bind(this)
    );
};

// Returns true if the item id should be included in the accessory list
// id: the Indigo ID of the device/action
IndigoPlatform.prototype.includeItemId = function(id) {
    if (this.includeIds && (this.includeIds.indexOf(String(id)) < 0)) {
        return false;
    }

    if (this.excludeIds && (this.excludeIds.indexOf(String(id)) >= 0)) {
        return false;
    }

    return true;
};

// Returns true if the item id should treat on and off as inverted in meaning
// id: the Indigo ID of the device/action
IndigoPlatform.prototype.invertOnOffId = function(id) {
    return (this.invertOnOffIds && (this.invertOnOffIds.indexOf(String(id)) >= 0));
};

// Makes a request to Indigo using the RESTful API
// path: the path of the request, relative to the base URL in the configuration, starting with a /
// method: the type of HTTP request to make (e.g. GET, POST, etc.)
// qs: the query string to include in the request (optional)
// callback: invokes callback(error, response, body) with the result of the HTTP request
IndigoPlatform.prototype.indigoRequest = function(path, method, qs, callback) {
    // seems to be a bug in request that if followRedirect is false and auth is
    // required, it crashes because redirects is missing, so I include it here
    var options = {
        url: this.baseURL + path,
        method: method,
        followRedirect: false,
        redirects: []
    };
    if (this.auth) {
        options.auth = this.auth;
    }
    if (qs) {
        options.qs = qs;
    }

    // All requests to Indigo are serialized, so that there is no more than one outstanding request at a time
    this.requestQueue.push(options, callback);
};

// Makes a request to Indigo using the RESTful API and parses the JSON response
// path: the path of the request, relative to the base URL in the configuration, starting with a /
// method: the type of HTTP request to make (e.g. GET, POST, etc.)
// qs: the query string to include in the request (optional)
// callback: invokes callback(error, json) with the parsed JSON object returned by the HTTP request
// jsonFixer: optional function which manipulates the HTTP response body before attempting to parse the JSON
//            this is used to work around bugs in Indigo's RESTful API responses that cause invalid JSON
IndigoPlatform.prototype.indigoRequestJSON = function(path, method, qs, callback, jsonFixer) {
    this.indigoRequest(path, method, qs,
        function(error, response, body) {
            if (error) {
                var msg = "Error for Indigo request " + path + ": " + error;
                this.log(msg);
                callback(msg);
            }
            else {
                if (jsonFixer) {
                    body = jsonFixer(body);
                }
                var json;
                try {
                    var json = JSON.parse(body);
                } catch (e) {
                    var msg2 = "Error parsing Indigo response for " + path +
                               "\nException: " + e + "\nResponse: " + body;
                    this.log(msg2);
                    callback(msg2);
                    return;
                }
                callback(undefined, json);
            }
        }.bind(this)
    );
};

// Returns subclass of IndigoAccessory based on json, or null if unsupported type
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
IndigoPlatform.prototype.createAccessoryFromJSON = function(deviceURL, json) {
    if (json.restParent == "actions") {
        return new IndigoActionAccessory(this, deviceURL, json);
    } else if (json.typeSupportsOnOff && this.treatAsSwitchIds &&
               (this.treatAsSwitchIds.indexOf(String(json.id)) >= 0)) {
        return new IndigoSwitchAccessory(this, deviceURL, json);
    } else if (json.typeSupportsOnOff && this.treatAsLockIds &&
               (this.treatAsLockIds.indexOf(String(json.id)) >= 0)) {
        return new IndigoLockAccessory(this, deviceURL, json);
    } else if (json.typeSupportsOnOff && this.treatAsDoorIds &&
               (this.treatAsDoorIds.indexOf(String(json.id)) >= 0)) {
        return new IndigoDoorAccessory(this, deviceURL, json);
    } else if (json.typeSupportsOnOff && this.treatAsGarageDoorIds &&
               (this.treatAsGarageDoorIds.indexOf(String(json.id)) >= 0)) {
        return new IndigoGarageDoorAccessory(this, deviceURL, json);
    } else if (json.typeSupportsOnOff && this.treatAsMotionSensorIds &&
               (this.treatAsMotionSensorIds.indexOf(String(json.id)) >= 0)) {
        return new IndigoMotionSensorAccessory(this, deviceURL, json);
    } else if (json.typeSupportsOnOff && this.treatAsContactSensorIds &&
               (this.treatAsContactSensorIds.indexOf(String(json.id)) >= 0)) {
        return new IndigoContactSensorAccessory(this, deviceURL, json);
    } else if (json.typeSupportsOnOff && this.treatAsWindowIds &&
               (this.treatAsWindowIds.indexOf(String(json.id)) >= 0)) {
        return new IndigoWindowAccessory(this, deviceURL, json);
    } else if (json.typeSupportsOnOff && this.treatAsWindowCoveringIds &&
               (this.treatAsWindowCoveringIds.indexOf(String(json.id)) >= 0)) {
        return new IndigoWindowCoveringAccessory(this, deviceURL, json);
    } else if (json.typeSupportsHVAC || json.typeIsHVAC) {
        return new IndigoThermostatAccessory(this, deviceURL, json, this.thermostatsInCelsius);
    } else if (json.typeSupportsSpeedControl || json.typeIsSpeedControl) {
        return new IndigoFanAccessory(this, deviceURL, json);
    } else if (json.typeSupportsDim || json.typeIsDimmer || json.typeSupportsOnOff) {
        return new IndigoLightAccessory(this, deviceURL, json);
    } else {
        return null;
    }
};

// Invoked by a GET request on listenPort of /devices/:id
// If the ID corresponds to an accessory, invokes refresh() on that accessory
// Sends a 200 HTTP response if successful, a 404 if the ID is not found, or a 500 if there is an error
IndigoPlatform.prototype.updateAccessory = function(request, response) {
    var id = String(request.params.id);
    this.log("Got update request for device ID %s", id);
    var accessory = this.accessoryMap.get(id);
    if (accessory) {
        accessory.refresh(function(error) {
            if (error) {
                this.log("Error updating device ID %s: %s", id, error);
                response.sendStatus(500);
            } else {
                response.sendStatus(200);
            }
        }.bind(this));
    }
    else {
        response.sendStatus(404);
    }
};

// Invoked by a POST request to listenPort of /devices/:id
// If the ID corresponds to an accessory, invokes refreshFromJSON() on that accessory with the POST body content (JSON)
// Unknown properties in the post body are silently ignored
// Sends a 200 HTTP response if successful, or a 404 if the ID is not found
IndigoPlatform.prototype.updateAccessoryFromPost = function(request, response) {
    var id = String(request.params.id);
    this.log("Got update request for device ID %s", id);
    var accessory = this.accessoryMap.get(id);
    if (accessory) {
        accessory.refreshFromJSON(request.body);
        response.sendStatus(200);
    }
    else {
        response.sendStatus(404);
    }
};


//
// Generic Indigo Accessory
//
// platform: the HomeKit platform
// serviceType: the constructor for the type of HAP service to create
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoAccessory(platform, serviceType, deviceURL, json) {
    this.platform = platform;
    this.log = platform.log;
    this.deviceURL = deviceURL;

    this.updateFromJSON(json);

    this.invertOnOff = platform.invertOnOffId(this.id);
    if (this.invertOnOff) {
        this.log("%s: Inverting on/off for this device", this.name);
    }

    Accessory.call(this, this.name, uuid.generate(String(this.id)));

    this.infoService = this.getService(Service.AccessoryInformation);
    this.infoService.setCharacteristic(Characteristic.Manufacturer, "Indigo")
        .setCharacteristic(Characteristic.SerialNumber, String(this.id));

    if (this.type) {
        this.infoService.setCharacteristic(Characteristic.Model, this.type);
    }

    if (this.versByte) {
        this.infoService.setCharacteristic(Characteristic.FirmwareRevision, this.versByte);
    }

    this.service = this.addService(serviceType, this.name);
}

// A set context that indicates this is from an update made by this plugin, so do not call the Indigo RESTful API with a put request
IndigoAccessory.REFRESH_CONTEXT = 'refresh';


// Returns the HomeKit services that this accessory supports
IndigoAccessory.prototype.getServices = function() {
    return this.services;
};

// Updates the Accessory's properties with values from JSON from the Indigo RESTful API
// json: JSON object from the Indigo RESTful API
// updateCallback: optional, invokes updateCallback(propertyName, propertyValue) for each property that has changed value
IndigoAccessory.prototype.updateFromJSON = function(json, updateCallback) {
    for (var prop in json) {
        if (prop != "name" && json.hasOwnProperty(prop)) {
            if (json[prop] != this[prop]) {
                this[prop] = json[prop];
                if (updateCallback) {
                    updateCallback(prop, json[prop]);
                }
            }
        }
    }

    // Allows us to change the name of accessories - useful for testing
    if (json.name !== undefined) {
        this.name = this.platform.accessoryNamePrefix + String(json.name);
    }
};

// Calls the Indigo RESTful API to get the latest state for this Accessory, and updates the Accessory's properties to match
// callback: invokes callback(error), error is undefined if no error occurred
// updateCallback: optional, invokes updateCallback(propertyName, propertyValue) for each property that has changed value
IndigoAccessory.prototype.getStatus = function(callback, updateCallback) {
    this.platform.indigoRequestJSON(this.deviceURL, "GET", null,
        function(error, json) {
            if (error) {
                if (callback) {
                    callback(error);
                }
            } else {
                this.updateFromJSON(json, updateCallback);
                if (callback) {
                    callback();
                }
            }
        }.bind(this)
    );
};

// Calls the Indigo RESTful API to alter the state of this Accessory, and updates the Accessory's properties to match
// qs: the query string parameters to send to the Indigo RESTful API via a PUT request
// callback: invokes callback(error), error is undefined if no error occurred
// updateCallback: optional, invokes updateCallback(propertyName, propertyValue) for each property that has changed value
IndigoAccessory.prototype.updateStatus = function(qs, callback, updateCallback) {
    this.log("updateStatus of %s: %s", this.name, JSON.stringify(qs));
    this.platform.indigoRequest(this.deviceURL, "PUT", qs,
        function(error, response, body) {
            if (error) {
                if (callback) {
                    callback(error);
                }
            } else {
                this.getStatus(callback, updateCallback);
            }
        }.bind(this)
    );
};
// Calls the Indigo RESTful API to get the latest state of this Accessory, and updates the Accessory's properties to match
// key: the property we are interested in
// callback: invokes callback(error, value), error is undefined if no error occurred, value is the value of the property named key
IndigoAccessory.prototype.query = function(key, callback) {
    this.getStatus(
        function(error) {
            if (error) {
                if (callback) {
                    callback(error);
                }
            } else {
                this.log("%s: query(%s) => %s", this.name, key, this[key]);
                if (callback) {
                    callback(undefined, this[key]);
                }
            }
        }.bind(this)
    );
};

// Invokes the Accessory's update_XXX(value) function, if it exists, where "XXX" is the value of prop
// For example, updateProperty("brightness", 100) invokes update_brightness(100) if the function update_brightess exists
// prop: the property name
// value: the property value
// TODO: Need a more elegant way to map HomeKit Characteristics and values to Indigo JSON keys and values
IndigoAccessory.prototype.updateProperty = function(prop, value) {
    updateFunction = "update_" + prop;
    if (this[updateFunction]) {
        this.log("%s: %s(%s)", this.name, updateFunction, value);
        this[updateFunction](value);
    }
};

// Calls the Indigo RESTful API to get the latest state of this Accessory, and updates the Accessory's properties to match
// Invokes the Accessory's update_KEY function for each property KEY where the value has changed from the prior cached state
// If the Accessory does not have an update_KEY function for a given KEY, it is safely ignored
// This is used when we are listening on the listenPort for notifications from Indigo about devices that have changed state
// callback: invokes callback(error), error is undefined if no error occurred
IndigoAccessory.prototype.refresh = function(callback) {
    this.log("%s: refresh()", this.name);
    this.getStatus(callback, this.updateProperty.bind(this));
};

// Updates the Accessory's properties to match the provided JSON key/value pairs
// Invokes the Accessory's update_KEY function for each property KEY where the value has changed from the prior cached state
// If the Accessory does not have an update_KEY function for a given KEY, it is safely ignored
// This is used when we are listening on the listenPort for notifications from Indigo about devices that have changed state
// json: the JSON key/value pairs to update
IndigoAccessory.prototype.refreshFromJSON = function(json) {
    this.log("%s: refreshFromJSON()", this.name);
    this.updateFromJSON(json, this.updateProperty.bind(this));
};


// Conversions that support inverted definitions of on/off and brightness

// Converts the value of Indigo's isOn parameter to some other constants representing on and off.
// isOn: Evaluated as a boolean
// onValue: Value to return for true
// offValue: Value to return for false
// Returns onValue if isOn evaluates to true, and offValue if isOn evaluates to false.
// NOTE: If this accessory is configured to invert on/off values, onValue is returned if isOn evaluates to false,
// and offValue is returned if isOn evaluates to true.
IndigoAccessory.prototype.convertIsOnToValue = function(isOn, onValue, offValue) {
    if (this.invertOnOff) {
        return ((isOn) ? offValue : onValue);
    } else {
        return ((isOn) ? onValue : offValue);
    }
}

// Converts the value of Indigo's isOn parameter to a boolean value.  Returns true or false.
// isOn: Evaluated as a boolean
// Returns true if isOn evaluates to true, and false if isOn evaluates to false.
// NOTE: If this accessory is configured to invert on/off values, true is returned if isOn evaluates to false,
// and false is returned if isOn evaluates to true.
IndigoAccessory.prototype.convertIsOnToBoolean = function(isOn) {
    return this.convertIsOnToValue(isOn, true, false);
}

// Converts a boolean expression to Indigo's isOn parameter values.  Returns 1 or 0.
// b: Evaluated as a boolean
// Returns 1 if b evaluates to true, and 0 if b evaluates to false.
// NOTE: If this accessory is configured to invert on/off values, 1 is returned if b evaluates to false,
// and 0 is returned if b evaluates to true.
IndigoAccessory.prototype.convertBooleanToIsOn = function(b) {
    if (this.invertOnOff) {
        return ((b) ? 0 : 1);
    } else {
        return ((b) ? 1 : 0);
    }
}

// Converts a brightness value to a possibly inverted value.
// brightness: The brightness value, between 0 (fully dark) and 100 (fully bright)
// Returns the brightness value
// NOTE: If this accessory is configured to invert on/off values, then 0 becomes fully bright and 100 becomes
// fully dark, so the inverted brightness value is returned.
IndigoAccessory.prototype.convertBrightness = function(brightness) {
    if (this.invertOnOff) {
        return (100 - brightness);
    } else {
        return (brightness);
    }
}


// Most accessories support on/off, so we include helper functions to get/set onState here

// Get the current on/off state of the accessory
// callback: invokes callback(error, onState)
//           error: error message or undefined if no error
//           onState: true if device is on, false otherwise
IndigoAccessory.prototype.getOnState = function(callback) {
    if (this.typeSupportsOnOff) {
        this.getStatus(
            function(error) {
                if (error) {
                    if (callback) {
                        callback(error);
                    }
                } else {
                    var onState = this.convertIsOnToBoolean(this.isOn);
                    this.log("%s: getOnState() => %s", this.name, onState);
                    if (callback) {
                        callback(undefined, onState);
                    }
                }
            }.bind(this)
        );
    }
    else if (callback) {
        callback("Accessory does not support on/off");
    }
};

// Set the current on/off state of the accessory
// onState: true if on, false otherwise
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, otherwise will
IndigoAccessory.prototype.setOnState = function(onState, callback, context) {
    this.log("%s: setOnState(%s)", this.name, onState);
    if (context == IndigoAccessory.REFRESH_CONTEXT) {
        if (callback) {
            callback();
        }
    } else if (this.typeSupportsOnOff) {
        this.updateStatus({ isOn: this.convertBooleanToIsOn(onState) }, callback);
    } else if (callback) {
        callback("Accessory does not support on/off");
    }
};


//
// Indigo Switch Accessory - Represents an on/off switch
//
// platform: the HomeKit platform
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoSwitchAccessory(platform, deviceURL, json) {
    IndigoAccessory.call(this, platform, Service.Switch, deviceURL, json);

    this.service.getCharacteristic(Characteristic.On)
        .on('get', this.getOnState.bind(this))
        .on('set', this.setOnState.bind(this));
}

// Update HomeKit state to match state of Indigo's isOn property
// isOn: new value of isOn property
IndigoSwitchAccessory.prototype.update_isOn = function(isOn) {
    this.service.getCharacteristic(Characteristic.On)
        .setValue(this.convertIsOnToBoolean(isOn), undefined, IndigoAccessory.REFRESH_CONTEXT);
};


//
// Indigo Lock Accessory - Represents a lock mechanism
//
// platform: the HomeKit platform
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoLockAccessory(platform, deviceURL, json) {
    IndigoAccessory.call(this, platform, Service.LockMechanism, deviceURL, json);

    this.service.getCharacteristic(Characteristic.LockCurrentState)
        .on('get', this.getLockCurrentState.bind(this));

    this.service.getCharacteristic(Characteristic.LockTargetState)
        .on('get', this.getLockTargetState.bind(this))
        .on('set', this.setLockTargetState.bind(this));
}

// Get the current lock state of the accessory
// callback: invokes callback(error, lockState)
//           error: error message or undefined if no error
//           lockState: Characteristic.LockCurrentState.SECURED (device on) or Characteristic.LockCurrentState.UNSECURED (device off)
IndigoLockAccessory.prototype.getLockCurrentState = function(callback) {
    if (this.typeSupportsOnOff) {
        this.getStatus(
            function(error) {
                if (error) {
                    if (callback) {
                        callback(error);
                    }
                } else {
                    var lockState = this.convertIsOnToValue(this.isOn, Characteristic.LockCurrentState.SECURED, Characteristic.LockCurrentState.UNSECURED);
                    this.log("%s: getLockCurrentState() => %s", this.name, lockState);
                    if (callback) {
                        callback(undefined, lockState);
                    }
                }
            }.bind(this)
        );
    }
    else if (callback) {
        callback("Accessory does not support on/off");
    }
};

// Get the target lock state of the accessory
// callback: invokes callback(error, lockState)
//           error: error message or undefined if no error
//           lockState: Characteristic.LockTargetState.SECURED (device on) or Characteristic.LockTargetState.UNSECURED (device off)
IndigoLockAccessory.prototype.getLockTargetState = function(callback) {
    if (this.typeSupportsOnOff) {
        this.getStatus(
            function(error) {
                if (error) {
                    if (callback) {
                        callback(error);
                    }
                } else {
                    var lockState = this.convertIsOnToValue(this.isOn, Characteristic.LockTargetState.SECURED, Characteristic.LockTargetState.UNSECURED);
                    this.log("%s: getLockTargetState() => %s", this.name, lockState);
                    if (callback) {
                        callback(undefined, lockState);
                    }
                }
            }.bind(this)
        );
    }
    else if (callback) {
        callback("Accessory does not support on/off");
    }
};

// Set the target lock state of the accessory
// lockState: Characteristic.LockTargetState.SECURED (device on) or Characteristic.LockTargetState.UNSECURED (device off)
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, and will not update LockCurrentState
//          otherwise, calls the Indigo RESTful API and also updates LockCurrentState to match after a one second delay
IndigoLockAccessory.prototype.setLockTargetState = function(lockState, callback, context) {
    this.log("%s: setLockTargetState(%s)", this.name, lockState);
    if (context == IndigoAccessory.REFRESH_CONTEXT) {
        if (callback) {
            callback();
        }
    }
    else if (this.typeSupportsOnOff) {
        this.updateStatus({ isOn: this.convertBooleanToIsOn(lockState == Characteristic.LockTargetState.SECURED) }, callback);
        // Update current state to match target state
        setTimeout(
            function() {
                this.service.getCharacteristic(Characteristic.LockCurrentState)
                    .setValue((lockState == Characteristic.LockTargetState.SECURED) ?
                                Characteristic.LockCurrentState.SECURED : Characteristic.LockCurrentState.UNSECURED,
                                undefined, IndigoAccessory.REFRESH_CONTEXT);
            }.bind(this),
        1000);
    }
    else if (callback) {
        callback("Accessory does not support on/off");
    }
};

// Update HomeKit state to match state of Indigo's isOn property
// isOn: new value of isOn property
IndigoLockAccessory.prototype.update_isOn = function(isOn) {
    this.service.getCharacteristic(Characteristic.LockCurrentState)
        .setValue(this.convertIsOnToValue(isOn, Characteristic.LockCurrentState.SECURED, Characteristic.LockCurrentState.UNSECURED),
                  undefined, IndigoAccessory.REFRESH_CONTEXT);
    this.service.getCharacteristic(Characteristic.LockTargetState)
        .setValue(this.convertIsOnToValue(isOn, Characteristic.LockTargetState.SECURED, Characteristic.LockTargetState.UNSECURED),
                  undefined, IndigoAccessory.REFRESH_CONTEXT);
};


//
// Indigo Position Accessory (Door, Window, or Window Covering)
//
// platform: the HomeKit platform
// serviceType: the constructor for the type of HAP service to create
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoPositionAccessory(platform, serviceType, deviceURL, json) {
    IndigoAccessory.call(this, platform, serviceType, deviceURL, json);

    this.service.getCharacteristic(Characteristic.CurrentPosition)
        .on('get', this.getPosition.bind(this));

    this.service.getCharacteristic(Characteristic.PositionState)
        .on('get', this.getPositionState.bind(this));

    this.service.getCharacteristic(Characteristic.TargetPosition)
        .on('get', this.getPosition.bind(this))
        .on('set', this.setTargetPosition.bind(this));
}

// Get the position of the accessory
// callback: invokes callback(error, position)
//           error: error message or undefined if no error
//           position: if device supports brightness, will return the brightness value; otherwise on=100 and off=0
IndigoPositionAccessory.prototype.getPosition = function(callback) {
    if (this.typeSupportsOnOff || this.typeSupportsDim || this.typeIsDimmer) {
        this.getStatus(
            function(error) {
                if (error) {
                    if (callback) {
                        callback(error);
                    }
                } else {
                    var position = this.convertIsOnToValue(this.isOn, 100, 0);
                    if (this.typeSupportsDim || this.typeIsDimmer) {
                        position = this.convertBrightness(this.brightness);
                    }
                    this.log("%s: getPosition() => %s", this.name, position);
                    if (callback) {
                        callback(undefined, position);
                    }
                }
            }.bind(this)
        );
    }
    else if (callback) {
        callback("Accessory does not support on/off or dim");
    }
};

// Get the position state of the accessory
// callback: invokes callback(error, position)
//           error: error message or undefined if no error
//           positionState: always Characteristic.PositionState.STOPPED
IndigoPositionAccessory.prototype.getPositionState = function(callback) {
    if (this.typeSupportsOnOff || this.typeSupportsDim || this.typeIsDimmer) {
        this.log("%s: getPositionState() => %s", this.name, Characteristic.PositionState.STOPPED);
        if (callback) {
            callback(undefined, Characteristic.PositionState.STOPPED);
        }
    }
    else if (callback) {
        callback("Accessory does not support on/off or dim");
    }
};

// Set the target position of the accessory
// position: if device supports brightness, sets brightness to equal position; otherwise turns device on if position > 0, or off otherwise
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, and will not update CurrentPosition
//          otherwise, calls the Indigo RESTful API and also updates CurrentPosition to match position after a one second delay
IndigoPositionAccessory.prototype.setTargetPosition = function(position, callback, context) {
    this.log("%s: setTargetPosition(%s)", this.name, position);
    if (context == IndigoAccessory.REFRESH_CONTEXT) {
        if (callback) {
            callback();
        }
    }
    else if (this.typeSupportsOnOff || this.typeSupportsDim || this.typeIsDimmer) {
        if (this.typeSupportsDim || this.typeIsDimmer) {
            this.updateStatus({ brightness: this.convertBrightness(position) }, callback);
        } else {
            this.updateStatus({ isOn: this.convertBooleanToIsOn(position > 0) }, callback);
        }
        // Update current state to match target state
        setTimeout(
            function() {
                this.service
                    .getCharacteristic(Characteristic.CurrentPosition)
                    .setValue(position, undefined, IndigoAccessory.REFRESH_CONTEXT);
            }.bind(this),
        1000);
    }
    else if (callback) {
        callback("Accessory does not support on/off or dim");
    }
};

// Update HomeKit state to match state of Indigo's isOn property
// Does nothing if device supports brightness
// isOn: new value of isOn property
IndigoPositionAccessory.prototype.update_isOn = function(isOn) {
    if (! (this.typeSupportsDim || this.typeIsDimmer)) {
        var position = this.convertIsOnToValue(isOn, 100, 0);
        this.service
            .getCharacteristic(Characteristic.CurrentPosition)
            .setValue(position, undefined, IndigoAccessory.REFRESH_CONTEXT);
        this.service
            .getCharacteristic(Characteristic.TargetPosition)
            .setValue(position, undefined, IndigoAccessory.REFRESH_CONTEXT);
    }
};

// Update HomeKit state to match state of Indigo's brightness property
// brightness: new value of brightness property
IndigoPositionAccessory.prototype.update_brightness = function(brightness) {
    var position = this.convertBrightness(brightness);
    this.service
        .getCharacteristic(Characteristic.CurrentPosition)
        .setValue(position, undefined, IndigoAccessory.REFRESH_CONTEXT);
    this.service
        .getCharacteristic(Characteristic.TargetPosition)
        .setValue(position, undefined, IndigoAccessory.REFRESH_CONTEXT);
};


//
// Indigo Door Accessory
//
// platform: the HomeKit platform
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoDoorAccessory(platform, deviceURL, json) {
    IndigoPositionAccessory.call(this, platform, Service.Door, deviceURL, json);
}


//
// Indigo Window Accessory
//
// platform: the HomeKit platform
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoWindowAccessory(platform, deviceURL, json) {
    IndigoPositionAccessory.call(this, platform, Service.Window, deviceURL, json);
}


//
// Indigo Window Covering Accessory
//
// platform: the HomeKit platform
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoWindowCoveringAccessory(platform, deviceURL, json) {
    IndigoPositionAccessory.call(this, platform, Service.WindowCovering, deviceURL, json);
}


//
// Indigo Garage Door Accessory
//
// platform: the HomeKit platform
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoGarageDoorAccessory(platform, deviceURL, json) {
    IndigoAccessory.call(this, platform, Service.GarageDoorOpener, deviceURL, json);

    this.service.getCharacteristic(Characteristic.CurrentDoorState)
        .on('get', this.getCurrentDoorState.bind(this));

    this.service.getCharacteristic(Characteristic.TargetDoorState)
        .on('get', this.getTargetDoorState.bind(this))
        .on('set', this.setTargetDoorState.bind(this));

    this.service.getCharacteristic(Characteristic.ObstructionDetected)
        .on('get', this.getObstructionDetected.bind(this));
}

// Get the current door state of the accessory
// callback: invokes callback(error, doorState)
//           error: error message or undefined if no error
//           doorState: Characteristic.CurrentDoorState.OPEN (device on) or Characteristic.CurrentDoorState.CLOSED (device off)
IndigoGarageDoorAccessory.prototype.getCurrentDoorState = function(callback) {
    if (this.typeSupportsOnOff) {
        this.getStatus(
            function(error) {
                if (error) {
                    if (callback) {
                        callback(error);
                    }
                } else {
                    var doorState = this.convertIsOnToValue(this.isOn, Characteristic.CurrentDoorState.OPEN, Characteristic.CurrentDoorState.CLOSED);
                    this.log("%s: getPosition() => %s", this.name, doorState);
                    if (callback) {
                        callback(undefined, doorState);
                    }
                }
            }.bind(this)
        );
    }
    else if (callback) {
        callback("Accessory does not support on/off");
    }
};

// Get the target door state of the accessory
// callback: invokes callback(error, doorState)
//           error: error message or undefined if no error
//           doorState: Characteristic.TargetDoorState.OPEN (device on) or Characteristic.TargetDoorState.CLOSED (device off)
IndigoGarageDoorAccessory.prototype.getTargetDoorState = function(callback) {
    if (this.typeSupportsOnOff) {
        this.getStatus(
            function(error) {
                if (error) {
                    if (callback) {
                        callback(error);
                    }
                } else {
                    var doorState = this.convertIsOnToValue(this.isOn, Characteristic.TargetDoorState.OPEN, Characteristic.TargetDoorState.CLOSED);
                    this.log("%s: getPosition() => %s", this.name, doorState);
                    if (callback) {
                        callback(undefined, doorState);
                    }
                }
            }.bind(this)
        );
    }
    else if (callback) {
        callback("Accessory does not support on/off");
    }
};

// Set the target door state of the accessory
// lockState: Characteristic.TargetDoorState.OPEN (device on) or Characteristic.TargetDoorState.CLOSED (device off)
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, and will not update CurrentDoorState
//          otherwise, calls the Indigo RESTful API and also updates CurrentDoorState to match after a one second delay
IndigoGarageDoorAccessory.prototype.setTargetDoorState = function(doorState, callback, context) {
    this.log("%s: setTargetPosition(%s)", this.name, doorState);
    if (context == IndigoAccessory.REFRESH_CONTEXT) {
        if (callback) {
            callback();
        }
    }
    else if (this.typeSupportsOnOff) {
        this.updateStatus({ isOn: this.convertBooleanToIsOn(doorState == Characteristic.TargetDoorState.OPEN) }, callback);
        // Update current state to match target state
        setTimeout(
            function() {
                this.service.getCharacteristic(Characteristic.CurrentDoorState)
                    .setValue((doorState == Characteristic.TargetDoorState.OPEN) ?
                                Characteristic.CurrentDoorState.OPEN : Characteristic.CurrentDoorState.CLOSED,
                                undefined, IndigoAccessory.REFRESH_CONTEXT);
            }.bind(this),
        1000);
    }
    else if (callback) {
        callback("Accessory does not support on/off");
    }
};

// Get the obstruction detected state of the accessory
// callback: invokes callback(error, obstructionDetected)
//           error: error message or undefined if no error
//           obstructionDetected: always false
IndigoGarageDoorAccessory.prototype.getObstructionDetected = function(callback) {
    if (this.typeSupportsOnOff) {
        this.log("%s: getObstructionDetected() => %s", this.name, false);
        if (callback) {
            callback(undefined, false);
        }
    }
    else if (callback) {
        callback("Accessory does not support on/off");
    }
};

// Update HomeKit state to match state of Indigo's isOn property
// isOn: new value of isOn property
IndigoGarageDoorAccessory.prototype.update_isOn = function(isOn) {
    this.service.getCharacteristic(Characteristic.CurrentDoorState)
        .setValue(this.convertIsOnToValue(isOn, Characteristic.CurrentDoorState.OPEN, Characteristic.CurrentDoorState.CLOSED),
                  undefined, IndigoAccessory.REFRESH_CONTEXT);
    this.service.getCharacteristic(Characteristic.TargetDoorState)
        .setValue(this.convertIsOnToValue(isOn, Characteristic.TargetDoorState.OPEN, Characteristic.TargetDoorState.CLOSED),
                  undefined, IndigoAccessory.REFRESH_CONTEXT);
};


//
// Indigo Motion Sensor Accessory
//
// platform: the HomeKit platform
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoMotionSensorAccessory(platform, deviceURL, json) {
    IndigoAccessory.call(this, platform, Service.MotionSensor, deviceURL, json);

    this.service.getCharacteristic(Characteristic.MotionDetected)
        .on('get', this.getOnState.bind(this));
}

// Update HomeKit state to match state of Indigo's isOn property
// isOn: new value of isOn property
IndigoMotionSensorAccessory.prototype.update_isOn = function(isOn) {
    this.service.getCharacteristic(Characteristic.MotionDetected)
        .setValue(this.convertIsOnToBoolean(isOn), undefined, IndigoAccessory.REFRESH_CONTEXT);
};


//
// Indigo Contact Sensor Accessory
//
// platform: the HomeKit platform
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoContactSensorAccessory(platform, deviceURL, json) {
    IndigoAccessory.call(this, platform, Service.ContactSensor, deviceURL, json);

    this.service.getCharacteristic(Characteristic.ContactSensorState)
        .on('get', this.getOnState.bind(this));
}

// Update HomeKit state to match state of Indigo's isOn property
// isOn: new value of isOn property
IndigoContactSensorAccessory.prototype.update_isOn = function(isOn) {
    this.service.getCharacteristic(Characteristic.ContactSensorState)
        .setValue(this.convertIsOnToBoolean(isOn), undefined, IndigoAccessory.REFRESH_CONTEXT);
};


//
// Indigo Light Accessory
//
// platform: the HomeKit platform
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoLightAccessory(platform, deviceURL, json) {
    IndigoAccessory.call(this, platform, Service.Lightbulb, deviceURL, json);

    if (this.brightness) {
        this.previousBrightness = this.brightness;
    }

    this.service.getCharacteristic(Characteristic.On)
        .on('get', this.getOnState.bind(this))
        .on('set', this.setLightOnState.bind(this));

    if (this.typeSupportsDim || this.typeIsDimmer) {
        this.service.getCharacteristic(Characteristic.Brightness)
            .on('get', this.getBrightness.bind(this))
            .on('set', this.setBrightness.bind(this));
    }
}

// Set the on state of the light
// onState: true if on, false otherwise
//          if true, sets the brightness to the previous brightness level, unless it is undefined or zero, in which case sends an ON command
//          this hackery is because HomeKit sends both ON and BRIGHTNESS when adjusting a light's brightness
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, otherwise will
IndigoLightAccessory.prototype.setLightOnState = function(onState, callback, context) {
    this.log("%s: setLightOnState(%d)", this.name, onState);
    if ((this.typeSupportsDim || this.typeIsDimmer) && onState && this.previousBrightness) {
        this.setBrightness(this.previousBrightness, callback, context);
    } else {
        this.setOnState(onState, callback, context)
    }
};

// Get the brightness of the accessory
// callback: invokes callback(error, brightness)
//           error: error message or undefined if no error
//           brightness: if device supports brightness, will return the brightness value
IndigoLightAccessory.prototype.getBrightness = function(callback) {
    if (this.typeSupportsDim || this.typeIsDimmer) {
        this.query("brightness",
            function(error, brightness) {
                if (!error && brightness > 0) {
                    this.previousBrightness = brightness;
                }
                if (callback) {
                    callback(error, this.convertBrightness(brightness));
                }
            }.bind(this)
        );
    } else if (callback) {
        callback("Accessory does not support brightness");
    }
};

// Set the current brightness of the accessory
// brightness: the brightness, from 0 (off) to 100 (full on)
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, otherwise will
IndigoLightAccessory.prototype.setBrightness = function(brightness, callback, context) {
    this.log("%s: setBrightness(%d)", this.name, brightness);
    if (context == IndigoAccessory.REFRESH_CONTEXT) {
        if (callback) {
            callback();
        }
    }
    else if (this.typeSupportsDim || this.typeIsDimmer) {
        if (brightness >= 0 && brightness <= 100) {
            if (brightness > 0) {
                this.previousBrightness = brightness;
            }
            this.updateStatus({brightness: this.convertBrightness(brightness)}, callback);
        }
    }
    else if (callback) {
        callback("Accessory does not support brightness");
    }
};

// Update HomeKit state to match state of Indigo's isOn property
// isOn: new value of isOn property
IndigoLightAccessory.prototype.update_isOn = function(isOn) {
    this.service.getCharacteristic(Characteristic.On)
        .setValue(this.convertIsOnToBoolean(isOn), undefined, IndigoAccessory.REFRESH_CONTEXT);
};

// Update HomeKit state to match state of Indigo's brightness property
// brightness: new value of brightness property
IndigoLightAccessory.prototype.update_brightness = function(brightness) {
    if (brightness > 0) {
        this.previousBrightness = brightness;
    }
    this.service.getCharacteristic(Characteristic.Brightness)
        .setValue(this.convertBrightness(brightness), undefined, IndigoAccessory.REFRESH_CONTEXT);
};


//
// Indigo Fan Accessory
//
// platform: the HomeKit platform
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoFanAccessory(platform, deviceURL, json) {
    IndigoAccessory.call(this, platform, Service.Fan, deviceURL, json);

    if (this.speedIndex) {
        this.previousRotationSpeed = (this.speedIndex / 3.0) * 100.0;
    }

    this.service.getCharacteristic(Characteristic.On)
        .on('get', this.getOnState.bind(this))
        .on('set', this.setFanOnState.bind(this));

    this.service.getCharacteristic(Characteristic.RotationSpeed)
        .on('get', this.getRotationSpeed.bind(this))
        .on('set', this.setRotationSpeed.bind(this));
}

// Set the on state of the fan
// onState: true if on, false otherwise
//          if true, sets the speed index to the previous speed index level, unless it is undefined or zero, in which case sends an ON command
//          this hackery is because HomeKit sends both ON and ROTATION SPEED when adjusting a fan's speed
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, otherwise will
IndigoFanAccessory.prototype.setFanOnState = function(onState, callback, context) {
    this.log("%s: setFanOnState(%d)", this.name, onState);
    if (onState && this.previousRotationSpeed) {
        this.setRotationSpeed(this.previousRotationSpeed, callback, context);
    } else {
        this.setOnState(onState, callback, context)
    }
};

// Get the rotation speed of the accessory
// callback: invokes callback(error, speedIndex)
//           error: error message or undefined if no error
//           speedIndex: if device supports speed control, will return the speed as a value from 0 (off) to 100 (full speed)
IndigoFanAccessory.prototype.getRotationSpeed = function(callback) {
    if (this.typeSupportsSpeedControl || this.typeIsSpeedControl) {
        this.query("speedIndex",
            function(error, speedIndex) {
                if (error) {
                    if (callback) {
                        callback(error);
                    }
                } else {
                    var rotationSpeed = (speedIndex / 3.0) * 100.0;
                    if (rotationSpeed > 0) {
                        this.previousRotationSpeed = rotationSpeed;
                    }
                    if (callback) {
                        callback(undefined, this.convertBrightness(rotationSpeed));
                    }
                }
            }.bind(this)
        );
    }
    else if (callback) {
        callback("Accessory does not support rotation speed");
    }
};

// Set the current rotation speed of the accessory
// rotationSpeed: the rotation speed, from 0 (off) to 100 (full speed)
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, otherwise will
IndigoFanAccessory.prototype.setRotationSpeed = function(rotationSpeed, callback, context) {
    this.log("%s: setRotationSpeed(%d)", this.name, rotationSpeed);
    if (context == IndigoAccessory.REFRESH_CONTEXT) {
        if (callback) {
            callback();
        }
    }
    else if (this.typeSupportsSpeedControl || this.typeIsSpeedControl) {
        if (rotationSpeed >= 0.0 && rotationSpeed <= 100.0) {
            var rs = this.convertBrightness(rotationSpeed);
            var speedIndex = 0;
            if (rs > (100.0 / 3.0 * 2.0)) {
                speedIndex = 3;
            } else if (rs > (100.0 / 3.0)) {
                speedIndex = 2;
            } else if (rs > 0) {
                speedIndex = 1;
            }
            if (rotationSpeed > 0) {
                this.previousRotationSpeed = rotationSpeed;
            }
            this.updateStatus({speedIndex: speedIndex}, callback);
        }
    }
    else if (callback) {
        callback("Accessory does not support rotation speed");
    }
};

// Update HomeKit state to match state of Indigo's isOn property
// isOn: new value of isOn property
IndigoFanAccessory.prototype.update_isOn = function(isOn) {
    this.service.getCharacteristic(Characteristic.On)
        .setValue(this.convertIsOnToBoolean(isOn), undefined, IndigoAccessory.REFRESH_CONTEXT);
};

// Update HomeKit state to match state of Indigo's speedIndex property
// speedIndex: new value of speedIndex property
IndigoFanAccessory.prototype.update_speedIndex = function(speedIndex) {
    var rotationSpeed = (speedIndex / 3.0) * 100.0;
    if (rotationSpeed > 0) {
        this.previousRotationSpeed = rotationSpeed;
    }
    this.service.getCharacteristic(Characteristic.RotationSpeed)
        .setValue(this.convertBrightness(rotationSpeed), undefined, IndigoAccessory.REFRESH_CONTEXT);
};


//
// Indigo Thermostat Accessory
//
// platform: the HomeKit platform
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoThermostatAccessory(platform, deviceURL, json, thermostatsInCelsius) {
    IndigoAccessory.call(this, platform, Service.Thermostat, deviceURL, json);

    this.thermostatsInCelsius = thermostatsInCelsius;

    this.temperatureDisplayUnits = (thermostatsInCelsius) ?
        Characteristic.TemperatureDisplayUnits.CELSIUS :
        Characteristic.TemperatureDisplayUnits.FAHRENHEIT;

    this.service.getCharacteristic(Characteristic.CurrentHeatingCoolingState)
        .on('get', this.getCurrentHeatingCooling.bind(this));

    this.service.getCharacteristic(Characteristic.TargetHeatingCoolingState)
        .on('get', this.getTargetHeatingCooling.bind(this))
        .on('set', this.setTargetHeatingCooling.bind(this));

    this.service.getCharacteristic(Characteristic.CurrentTemperature)
        .setProps({minValue: -50})
        .on('get', this.getCurrentTemperature.bind(this));

    this.service.getCharacteristic(Characteristic.TargetTemperature)
        .on('get', this.getTargetTemperature.bind(this))
        .on('set', this.setTargetTemperature.bind(this));

    this.service.getCharacteristic(Characteristic.TemperatureDisplayUnits)
        .on('get', this.getTemperatureDisplayUnits.bind(this))
        .on('set', this.setTemperatureDisplayUnits.bind(this));

    this.service.getCharacteristic(Characteristic.CoolingThresholdTemperature)
        .on('get', this.getCoolingThresholdTemperature.bind(this))
        .on('set', this.setCoolingThresholdTemperature.bind(this));

    this.service.getCharacteristic(Characteristic.HeatingThresholdTemperature)
        .on('get', this.getHeatingThresholdTemperature.bind(this))
        .on('set', this.setHeatingThresholdTemperature.bind(this));

    if (this.displayHumidityInRemoteUI) {
        this.service.getCharacteristic(Characteristic.CurrentRelativeHumidity)
            .on('get', this.getCurrentRelativeHumidity.bind(this));
    }
}

// Determine the current heating/cooling state
// returns one of Characteristic.CurrentHeatingCoolingState.{OFF,HEAT,COOL}
IndigoThermostatAccessory.prototype.determineCurrentHeatingCoolingState = function() {
    var mode = Characteristic.CurrentHeatingCoolingState.OFF;
    if (this.hvacHeaterIsOn) {
        mode = Characteristic.CurrentHeatingCoolingState.HEAT;
    } else if (this.hvacCoolerIsOn) {
        mode = Characteristic.CurrentHeatingCoolingState.COOL;
    }
    return mode;
};

// Determine the target heating/cooling state
// returns one of Characteristic.TargetHeatingCoolingState.{OFF,HEAT,COOL,AUTO}
IndigoThermostatAccessory.prototype.determineTargetHeatingCoolingState = function() {
    var mode = Characteristic.TargetHeatingCoolingState.OFF;
    if (this.hvacOperationModeIsHeat || this.hvacOperationModeIsProgramHeat) {
        mode = Characteristic.TargetHeatingCoolingState.HEAT;
    } else if (this.hvacOperationModeIsCool || this.hvacOperationModeIsProgramCool) {
        mode = Characteristic.TargetHeatingCoolingState.COOL;
    } else if (this.hvacOperationModeIsAuto || this.hvacOperationModeIsProgramAuto) {
        mode = Characteristic.TargetHeatingCoolingState.AUTO;
    }
    return mode;
};

// Get the current heating/cooling state of the accessory
// callback: invokes callback(error, mode)
//           error: error message or undefined if no error
//           mode: one of Characteristic.CurrentHeatingCoolingState.{OFF,HEAT,COOL}
IndigoThermostatAccessory.prototype.getCurrentHeatingCooling = function(callback) {
    if (this.typeSupportsHVAC || this.typeIsHVAC) {
        this.getStatus(
            function (error) {
                if (error) {
                    if (callback) {
                        callback(error);
                    }
                } else {
                    var mode = this.determineCurrentHeatingCoolingState();
                    this.log("%s: getCurrentHeatingCooling() => %s", this.name, mode);
                    if (callback) {
                        callback(undefined, mode);
                    }
                }
            }.bind(this)
        );
    }
    else if (callback) {
        callback("Accessory does not support HVAC");
    }
};

// Get the target heating/cooling state of the accessory
// callback: invokes callback(error, mode)
//           error: error message or undefined if no error
//           mode: one of Characteristic.TargetHeatingCoolingState.{OFF,HEAT,COOL,AUTO}
IndigoThermostatAccessory.prototype.getTargetHeatingCooling = function(callback) {
    if (this.typeSupportsHVAC || this.typeIsHVAC) {
        this.getStatus(
            function (error) {
                if (error) {
                    if (callback) {
                        callback(error);
                    }
                } else {
                    var mode = this.determineTargetHeatingCoolingState();
                    this.log("%s: getTargetHeatingCooling() => %s", this.name, mode);
                    if (callback) {
                        callback(undefined, mode);
                    }
                }
            }.bind(this)
        );
    }
    else if (callback) {
        callback("Accessory does not support HVAC");
    }
};

// Set the target heating/cooling state of the accessory
// mode: one of Characteristic.TargetHeatingCoolingState.{OFF,HEAT,COOL,AUTO}
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, otherwise will
IndigoThermostatAccessory.prototype.setTargetHeatingCooling = function(mode, callback, context) {
    this.log("%s: setTargetHeatingCooling(%s)", this.name, mode);
    if (context == IndigoAccessory.REFRESH_CONTEXT) {
        if (callback) {
            callback();
        }
    }
    else if (this.typeSupportsHVAC || this.typeIsHVAC) {
        var hvacCurrentMode;
        if (mode == Characteristic.TargetHeatingCoolingState.OFF) {
            hvacCurrentMode = "all off";
        }
        else if (mode == Characteristic.TargetHeatingCoolingState.HEAT) {
            hvacCurrentMode = "heat on";
        }
        else if (mode == Characteristic.TargetHeatingCoolingState.COOL) {
            hvacCurrentMode = "cool on";
        }
        else if (mode == Characteristic.TargetHeatingCoolingState.AUTO) {
            hvacCurrentMode = "auto on";
        }

        if (hvacCurrentMode) {
            this.updateStatus({hvacCurrentMode: hvacCurrentMode}, callback);
        } else if (callback) {
            callback("Unknown target heating/cooling state");
        }
    }
    else if (callback) {
        callback("Accessory does not support HVAC");
    }
};

// Note: HomeKit wants all temperature values in celsius, so convert if needed

// Converts a celsius temperature into Indigo's units (F or C, depending on setting)
// temperature: temperature in degrees celsius
// returns: temperature in Indigo's units
IndigoThermostatAccessory.prototype.celsiusToIndigoTemp = function(temperature) {
    if (this.thermostatsInCelsius) {
        return (temperature);
    } else {
        return (Math.round(((temperature * 9.0 / 5.0) + 32.0) * 10.0) / 10.0);
    }
}

// Converts a temperature in Indigo's units (F or C, depending on setting) into celsius
// temperature: temperature in Indigo's units
// returns: temperature in degrees celsius
IndigoThermostatAccessory.prototype.indigoTempToCelsius = function(temperature) {
    if (this.thermostatsInCelsius) {
        return (temperature);
    } else {
        return (Math.round(((temperature - 32.0) * 5.0 / 9.0) * 10.0) / 10.0);
    }
}

// Invokes the Indigo RESTful API to get a temperature value
// key: the Indigo RESTful API response JSON key of the temperature value
// callback: invokes callback(error, temperature)
//           error: error message or undefined if no error
//           temperature: the temperature in degrees celsius
IndigoThermostatAccessory.prototype.getTemperatureValue = function(key, callback) {
    if (this.typeSupportsHVAC || this.typeIsHVAC) {
        this.query(key,
            function(error, temperature) {
                if (error) {
                    if (callback) {
                        callback(error);
                    }
                } else {
                    var t = this.indigoTempToCelsius(temperature);
                    this.log("%s: getTemperatureValue(%s) => %s", this.name, key, t);
                    if (callback) {
                        callback(undefined, t);
                    }
                }
            }.bind(this)
        );
    }
    else if (callback) {
        callback("Accessory does not support HVAC");
    }
};

// Invokes the Indigo RESTful API to update a temperature value
// key: the Indigo RESTful API JSON key of the temperature value to update
// temperature: the temperature in degrees celsius
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, otherwise will
IndigoThermostatAccessory.prototype.setTemperatureValue = function(key, temperature, callback, context) {
    this.log("%s: setTemperatureValue(%s, %s)", this.name, key, temperature);
    if (context == IndigoAccessory.REFRESH_CONTEXT) {
        if (callback) {
            callback();
        }
    }
    else if (this.typeSupportsHVAC || this.typeIsHVAC) {
        var qs = { };
        qs[key] = this.celsiusToIndigoTemp(temperature);
        this.updateStatus(qs, callback);
    }
    else if (callback) {
        callback("Accessory does not support HVAC");
    }
};


// Get the current temperature of the accessory
// callback: invokes callback(error, temperature)
//           error: error message or undefined if no error
//           temperature: the temperature in degrees celsius
IndigoThermostatAccessory.prototype.getCurrentTemperature = function(callback) {
    this.getTemperatureValue("inputTemperatureVals", callback);
};

// Determine the target temperature of the accessory
// If the thermostat is in heating mode, returns the heat setpoint in degrees celsius
// If the thermostat is in cooling mode, returns the cool setpoint in degrees celsius
// Otherwise, returns the average of the heat and cool setpoints in degrees celsius
IndigoThermostatAccessory.prototype.determineTargetTemperature = function() {
    var temperature;
    if (this.hvacOperationModeIsHeat || this.hvacOperationModeIsProgramHeat) {
        temperature = this.setpointHeat;
    }
    else if (this.hvacOperationModeIsCool || this.hvacOperationModeIsProgramCool) {
        temperature = this.setpointCool;
    }
    else {
        temperature = (this.setpointHeat + this.setpointCool) / 2.0;
    }
    return this.indigoTempToCelsius(temperature);
}

// Get the target temperature of the accessory
// If the thermostat is in heating mode, it uses the heat setpoint
// If the thermostat is in cooling mode, it uses the cool setpoint
// Otherwise, it uses the average of the heat and cool setpoints
// callback: invokes callback(error, temperature)
//           error: error message or undefined if no error
//           temperature: the temperature in degrees celsius
IndigoThermostatAccessory.prototype.getTargetTemperature = function(callback) {
    if (this.typeSupportsHVAC || this.typeIsHVAC) {
        this.getStatus(
            function (error) {
                if (error) {
                    if (callback) {
                        callback(error);
                    }
                } else {
                    var t = this.determineTargetTemperature();
                    this.log("%s: getTargetTemperature() => %s", this.name, t);
                    if (callback) {
                        callback(undefined, t);
                    }
                }
            }.bind(this)
        );
    }
    else if (callback) {
        callback("Accessory does not support HVAC");
    }
};

// Set the target temperature of the accessory
// If the thermostat is in heating mode, it sets the heat setpoint
// If the thermostat is in cooling mode, it sets the cool setpoint
// Otherwise, it sets the heat setpoint to 2 degrees celsius (5 degrees fahrenheit) below the target temperature,
// and sets the cool setpoint to 2 degrees celsius (5 degrees fahrenheit) above the target temperature
// temperature: the temperature in degrees celsius
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, otherwise will
IndigoThermostatAccessory.prototype.setTargetTemperature = function(temperature, callback, context) {
    this.log("%s: setTargetTemperature(%s)", this.name, temperature);
    if (context == IndigoAccessory.REFRESH_CONTEXT) {
        if (callback) {
            callback();
        }
    }
    else if (this.typeSupportsHVAC || this.typeIsHVAC) {
        var t = this.celsiusToIndigoTemp(temperature);
        this.getStatus(
            function (error) {
                if (error) {
                    if (callback) {
                        callback(error);
                    }
                } else {
                    var qs;
                    if (this.hvacOperationModeIsHeat) {
                        qs = {setpointHeat: t};
                    }
                    else if (this.hvacOperationModeIsCool) {
                        qs = {setpointCool: t};
                    }
                    else {
                        var adjust = (this.thermostatsInCelsius) ? 2 : 5;
                        qs = {setpointCool: t + adjust, setpointHeat: t - adjust};
                    }
                    this.updateStatus(qs, callback);
                }
            }.bind(this)
        );
    }
    else if (callback) {
        callback("Accessory does not support HVAC");
    }
};

// Get the temperature display units of the accessory
// callback: invokes callback(error, units)
//           error: error message or undefined if no error
//           units: the temperature display units - one of TemperatureDisplayUnits.{CELSIUS,FAHRENHEIT}
IndigoThermostatAccessory.prototype.getTemperatureDisplayUnits = function(callback) {
    this.log("%s: getTemperatureDisplayUnits() => %s", this.name, this.temperatureDisplayUnits);
    if (callback) {
        callback(undefined, this.temperatureDisplayUnits);
    }
};

// Set the temperature display units of the accessory
// units: the temperature display units - one of TemperatureDisplayUnits.{CELSIUS,FAHRENHEIT}
// callback: invokes callback(error), error is undefined if no error occurred
IndigoThermostatAccessory.prototype.setTemperatureDisplayUnits = function(units, callback) {
    this.log("%s: setTemperatureDisplayUnits(%s)", this.name, units);
    this.temperatureDisplayUnits = units;
    if (callback) {
        callback();
    }
};

// Get the cooling threshold temperature of the accessory
// callback: invokes callback(error, temperature)
//           error: error message or undefined if no error
//           temperature: the temperature in degrees celsius
IndigoThermostatAccessory.prototype.getCoolingThresholdTemperature = function(callback) {
    this.getTemperatureValue("setpointCool", callback);
};

// Set the cooling threshold temperature of the accessory
// temperature: the temperature in degrees celsius
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, otherwise will
IndigoThermostatAccessory.prototype.setCoolingThresholdTemperature = function(temperature, callback, context) {
    this.setTemperatureValue("setpointCool", temperature, callback, context);
};

// Get the heating threshold temperature of the accessory
// callback: invokes callback(error, temperature)
//           error: error message or undefined if no error
//           temperature: the temperature in degrees celsius
IndigoThermostatAccessory.prototype.getHeatingThresholdTemperature = function(callback) {
    this.getTemperatureValue("setpointHeat", callback);
};

// Set the heating threshold temperature of the accessory
// temperature: the temperature in degrees celsius
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to update the device, otherwise will
IndigoThermostatAccessory.prototype.setHeatingThresholdTemperature = function(temperature, callback, context) {
    this.setTemperatureValue("setpointHeat", temperature, callback, context);
};

// Get the current relative humidity of the accessory
// callback: invokes callback(error, relativeHumidity)
//           error: error message or undefined if no error
//           relativeHumidity: the relative humidity
IndigoThermostatAccessory.prototype.getCurrentRelativeHumidity = function(callback) {
    if (this.displayHumidityInRemoteUI) {
        this.query("inputHumidityVals", callback);
    } else if (callback) {
        callback("Accessory does not support relative humidity");
    }
};

// Update HomeKit state to match state of Indigo's hvacHeaterIsOn/hvacCoolerIsOn property
// prop: new value of property
IndigoThermostatAccessory.prototype.update_hvacHeaterIsOn =
IndigoThermostatAccessory.prototype.update_hvacCoolerIsOn = function(prop) {
    this.service.getCharacteristic(Characteristic.CurrentHeatingCoolingState)
        .setValue(this.determineCurrentHeatingCoolingState(), undefined, IndigoAccessory.REFRESH_CONTEXT);
};

// Update HomeKit state to match state of Indigo's hvacOperationModeIsHeat/hvacOperationModeIsProgramHeat
// hvacOperationModeIsCool/hvacOperationModeIsProgramCool/hvacOperationModeIsAuto/hvacOperationModeIsProgramAuto property
// prop: new value of property
IndigoThermostatAccessory.prototype.update_hvacOperationModeIsHeat =
IndigoThermostatAccessory.prototype.update_hvacOperationModeIsProgramHeat =
IndigoThermostatAccessory.prototype.update_hvacOperationModeIsCool =
IndigoThermostatAccessory.prototype.update_hvacOperationModeIsProgramCool =
IndigoThermostatAccessory.prototype.update_hvacOperationModeIsAuto =
IndigoThermostatAccessory.prototype.update_hvacOperationModeIsProgramAuto = function(prop) {
    this.service.getCharacteristic(Characteristic.TargetHeatingCoolingState)
        .setValue(this.determineTargetHeatingCoolingState(), undefined, IndigoAccessory.REFRESH_CONTEXT);
    this.service.getCharacteristic(Characteristic.TargetTemperature)
        .setValue(this.determineTargetTemperature(), undefined, IndigoAccessory.REFRESH_CONTEXT);
};

// Update HomeKit state to match state of Indigo's inputTemperatureVals property
// inputTemperatureVals: new value of inputTemperatureVals property
IndigoThermostatAccessory.prototype.update_inputTemperatureVals = function(inputTemperatureVals) {
    this.service.getCharacteristic(Characteristic.CurrentTemperature)
        .setValue(this.indigoTempToCelsius(inputTemperatureVals), undefined, IndigoAccessory.REFRESH_CONTEXT);
};

// Update HomeKit state to match state of Indigo's setpointCool property
// setpointCool: new value of setpointCool property
IndigoThermostatAccessory.prototype.update_setpointCool = function(setpointCool) {
    this.service.getCharacteristic(Characteristic.CoolingThresholdTemperature)
        .setValue(this.indigoTempToCelsius(setpointCool), undefined, IndigoAccessory.REFRESH_CONTEXT);
    this.service.getCharacteristic(Characteristic.TargetTemperature)
        .setValue(this.determineTargetTemperature(), undefined, IndigoAccessory.REFRESH_CONTEXT);
};

// Update HomeKit state to match state of Indigo's setpointHeat property
// setpointHeat: new value of setpointHeat property
IndigoThermostatAccessory.prototype.update_setpointHeat = function(setpointHeat) {
    this.service.getCharacteristic(Characteristic.HeatingThresholdTemperature)
        .setValue(this.indigoTempToCelsius(setpointHeat), undefined, IndigoAccessory.REFRESH_CONTEXT);
    this.service.getCharacteristic(Characteristic.TargetTemperature)
        .setValue(this.determineTargetTemperature(), undefined, IndigoAccessory.REFRESH_CONTEXT);
};

// Update HomeKit state to match state of Indigo's inputHumidityVals property
// inputHumidityVals: new value of inputHumidityVals property
IndigoThermostatAccessory.prototype.update_inputHumidityVals = function(inputHumidityVals) {
    this.service.getCharacteristic(Characteristic.CurrentRelativeHumidity)
        .setValue(inputHumidityVals, undefined, IndigoAccessory.REFRESH_CONTEXT);
};


//
// Indigo Action Accessory - Represents an Indigo action group as a "push button switch" accessory (turns on only momentarily)
//
// platform: the HomeKit platform
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// json: the json that describes this device
//
function IndigoActionAccessory(platform, deviceURL, json) {
    IndigoAccessory.call(this, platform, Service.Switch, deviceURL, json);

    this.service.getCharacteristic(Characteristic.On)
        .on('get', this.getActionState.bind(this))
        .on('set', this.executeAction.bind(this));
}

// Get the action state of the accessory
// Actions always say they are off
// callback: invokes callback(undefined, false)
IndigoActionAccessory.prototype.getActionState = function(callback) {
    this.log("%s: getActionState() => %s", this.name, false);
    callback(undefined, false);
};

// Executes the action if value is true and turns the accessory back off
// value: if true, executes the action and updates the accessory state back to off
// callback: invokes callback(error), error is undefined if no error occurred
// context: if equal to IndigoAccessory.REFRESH_CONTEXT, will not call the Indigo RESTful API to execute the action, otherwise will
IndigoActionAccessory.prototype.executeAction = function(value, callback, context) {
    this.log("%s: executeAction(%s)", this.name, value);
    if (value && context !== IndigoAccessory.REFRESH_CONTEXT) {
        this.platform.indigoRequest(this.deviceURL, "EXECUTE", null,
            function(error, response, body) {
                if (error) {
                    this.log("Error executing action group: %s", error);
                }
            }.bind(this)
        );

        // Turn the switch back off
        setTimeout(
            function() {
                this.service.getCharacteristic(Characteristic.On)
                    .setValue(false, undefined, IndigoAccessory.REFRESH_CONTEXT);
            }.bind(this),
        1000);
    }

    if (callback) {
        callback();
    }
};

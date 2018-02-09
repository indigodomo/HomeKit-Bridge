/*
Indigo2 platform shim for HomeBridge
Written by Mike Riccio (https://github.com/webdeck/homebridge-indigo)
See http://www.indigodomo.com/ for more info on Indigo
See http://forums.indigodomo.com/viewtopic.php?f=9&t=15008 for installation instructions

Configuration example for your Homebridge config.json:

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

Fields:
    "platform": Must always be "Indigo2" (required)
    "name": Can be anything (required)
    "protocol": "http" or "https" (optional, defaults to "http" if not specified)
    "host": Hostname or IP Address of your Indigo web server (required)
    "port": Port number of your HomeKit Bridge RESTful API server (required)
    "serverId": Identifier of the HomeKit Bridge server instance (required)
    "accessoryNamePrefix": Prefix all accessory names with this string (optional, useful for testing)
    "listenPort": homebridge-indigo2 will listen on this port for device state updates from HomeKit Bridge (required)
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

    fixInheritance(Indigo2Accessory, Accessory);

    homebridge.registerPlatform("homebridge-indigo2", "Indigo2", Indigo2Platform);
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
function Indigo2Platform(log, config) {
    this.log = log;

    // We use a queue to serialize all the requests to Indigo
    this.requestQueue = async.queue(
        function(options, callback) {
            this.log("HomeKit Bridge request: %s", options.url);
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

    var host = "127.0.0.1";
    if (config.host) {
        host = config.host;
    } else {
        this.log("WARNING: host not configured - using %s", host);
    }

    var port = "8558";
    if (config.port) {
        port = String(config.port);
    } else {
        this.log("WARNING: port not configured - using %s", port);
    }

    this.baseURL = protocol + "://" + config.host + ":" + port;
    this.log("HomeKit Bridge base URL is %s", this.baseURL);

    this.serverId = "0";
    if (config.serverId) {
        this.serverId = String(config.serverId);
        this.log("HomeKit Bridge serverId is %s", this.serverId)
    } else {
        this.log("WARNING: serverId not configured - using %s", this.serverId);
    }

    this.accessoryNamePrefix = "";
    if (config.accessoryNamePrefix) {
        this.accessoryNamePrefix = config.accessoryNamePrefix;
        this.log("Using accessory name prefix '%s'", this.accessoryNamePrefix)
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
    else {
        this.log("WARNING: listenPort not configured - not listening for updates")
    }
}

// Invokes callback(accessories[]) with all of the discovered accessories for this platform
Indigo2Platform.prototype.accessories = function(callback) {
    this.discoverAccessories(
        function (error) {
            if (error) {
                this.log(error);
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

// Discovers all of the accessories
// Populates this.foundAccessories and this.accessoryMap
// callback: invokes callback(error) when all accessories have been discovered; error is undefined if no error occurred
Indigo2Platform.prototype.discoverAccessories = function(callback) {
    this.indigoRequestJSON("/HomeKit?cmd=deviceList&serverId=" + this.serverId, "GET", null,
        function(error, json) {
            if (error) {
                callback(error);
            }
            else if (Array.isArray(json)) {
                json.forEach(this.addAccessory.bind(this));
                callback();
            }
            else {
                callback("Invalid response getting deviceList")
            }
        }.bind(this)
    );
};

// Adds an IndigoAccessory object to this.foundAccessories and this.accessoryMap
// item: JSON describing the device
Indigo2Platform.prototype.addAccessory = function(item) {
    var accessory = this.createAccessory(item);
    if (accessory) {
        this.foundAccessories.push(accessory);
        this.accessoryMap.set(accessory.id, accessory);
    }
};

Indigo2Platform.prototype.createAccessory = function(item) {
    var id = item.id;
    if (! id) {
        this.log("ERROR: Device missing id");
        return null;
    }
    id = String(id);

    var serviceName = item.hkservice;
    if (! serviceName) {
        this.log("ERROR: Device %s missing service name", id);
        return null;
    }
    serviceName = String(serviceName);

    var service = Service[serviceName];
    if (! service) {
        this.log("ERROR: Device %s has unknown Service name: %s", id, serviceName);
        return null;
    }

    var name = item.name;
    if (item.alias) {
        name = item.alias;
    }
    if (! name) {
        this.log("Error: Device %s has no name or alias", id);
        return null;
    }
    name = this.accessoryNamePrefix + String(name);

    var url = item.url;
    if (! url) {
        this.log("Error: Device %s has no url", id);
        return null;
    }
    url = String(url);

    var objectType = item.object;
    if (! objectType) {
        this.log("Error: Device %s has no object type", id);
        return null;
    }
    objectType = String(objectType);

    var characteristics = item.hkcharacteristics;
    if (! Array.isArray(characteristics)) {
        this.log("Error: Device %s has no characteristics", id);
        return null;
    }

    this.log("Discovered %s %s (ID %s): %s", objectType, serviceName, id, name);
    return new Indigo2Accessory(this, service, url, id, objectType, name, characteristics);
};

// Makes a request to Indigo using the RESTful API
// path: the path of the request, relative to the base URL in the configuration, starting with a /
// method: the type of HTTP request to make (e.g. GET, POST, etc.)
// qs: the query string to include in the request (optional)
// callback: invokes callback(error, response, body) with the result of the HTTP request
Indigo2Platform.prototype.indigoRequest = function(path, method, qs, callback) {
    // seems to be a bug in request that if followRedirect is false and auth is
    // required, it crashes because redirects is missing, so I include it here
    var options = {
        url: this.baseURL + path,
        method: method,
        followRedirect: false,
        redirects: []
    };
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
Indigo2Platform.prototype.indigoRequestJSON = function(path, method, qs, callback) {
    this.indigoRequest(path, method, qs,
        function(error, response, body) {
            if (error) {
                var msg = "Error for Indigo request " + path + ": " + error;
                this.log(msg);
                callback(msg);
            }
            else {
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

// Invoked by a GET request on listenPort of /devices/:id
// If the ID corresponds to an accessory, invokes refresh() on that accessory
// Sends a 200 HTTP response if successful, a 404 if the ID is not found, or a 500 if there is an error
Indigo2Platform.prototype.updateAccessory = function(request, response) {
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
Indigo2Platform.prototype.updateAccessoryFromPost = function(request, response) {
    var id = String(request.params.id);
    this.log("Got update request for device ID %s", id);
    var accessory = this.accessoryMap.get(id);
    if (accessory) {
        // TODO - use request.body after confirming contents w/CFW
        // accessory.refreshFromJSON(request.body);
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


//
// Generic Indigo Accessory
//
// platform: the HomeKit platform
// serviceType: the constructor for the type of HAP service to create
// deviceURL: the path of the RESTful call for this device, relative to the base URL in the configuration, starting with a /
// id: the unique identifier of the device
// objectType: the type of Indigo object (e.g. "Device", "Action", "Variable")
// name: the name of the device
// characteristics: the json array of characteristics for this device
//
function Indigo2Accessory(platform, serviceType, deviceURL, id, objectType, name, characteristics) {
    this.platform = platform;
    this.log = platform.log;
    this.serviceType = serviceType;
    this.deviceURL = deviceURL;
    this.id = id;
    this.objectType = objectType;
    this.name = name;
    this.characteristics = {};

    Accessory.call(this, name, uuid.generate(String(id)));

    this.infoService = this.getService(Service.AccessoryInformation);
    this.infoService.setCharacteristic(Characteristic.Manufacturer, "Indigo HomeKit Bridge")
        .setCharacteristic(Characteristic.SerialNumber, String(id));

    // TODO: Request type and versByte to be added to JSON to specify Model and FirmwareRevision
    if (this.type) {
        this.infoService.setCharacteristic(Characteristic.Model, type);
    }

    if (this.versByte) {
        this.infoService.setCharacteristic(Characteristic.FirmwareRevision, this.versByte);
    }

    this.service = this.addService(serviceType, name);
    characteristics.forEach(this.addCharacteristic.bind(this));
}

// Adds a characteristic to the accessory
// characteristic: JSON describing the characteristic to add
Indigo2Accessory.prototype.addCharacteristic = function(characteristic) {
    var name = characteristic.name;
    if (! name) {
        this.log("ERROR: Device %s missing Characteristic name", this.id);
        return;
    }
    name = String(name);

    var characteristicType = Characteristic[name];
    if (! characteristicType) {
        this.log("ERROR: Device %s has unknown Characteristic name: %s", this.id, name);
        return;
    }

    var c = this.service.getCharacteristic(characteristicType);
    if (! c) {
        this.log("ERROR: Device %s - error adding Characteristic name: %s", this.id, name);
        return;
    }

    this.characteristics[name] = characteristic;

    c.on('get', this.createGetter(name).bind(this));
    if (! characteristic.readonly) {
        c.on('set', this.createSetter(name).bind(this));
    }
};

// A set context that indicates this is from an update made by this plugin, so do not call the Indigo RESTful API with a put request
Indigo2Accessory.REFRESH_CONTEXT = 'refresh';

// Returns a function to get the current value of a characteristic
// characteristicName: The name of the characteristic
Indigo2Accessory.prototype.createGetter = function(characteristicName) {
    return function(callback) {
        var characteristic = this.characteristics[characteristicName];
        if (characteristic) {
            var value = characteristic.value;
            if (value !== undefined && value !== null) {
                this.log("%s: get(%s) => %s", this.name, characteristicName, value);
                if (callback) {
                    callback(undefined, value);
                }
            }
            else {
                this.log("%s: get(%s) => undefined", this.name, characteristicName);
                if (callback) {
                    callback("Undefined value for characteristic " + characteristicName);
                }
            }
        }
        else {
            this.log("ERROR: %s: get for unknown characteristic %s", this.name, characteristicName);
            if (callback) {
                callback("Unknown characteristic " + characteristicName);
            }
        }
    }.bind(this);
};

// Returns a function to set the current value of a characteristic
// characteristicName: The name of the characteristic
Indigo2Accessory.prototype.createSetter = function(characteristicName) {
    return function(value, callback, context) {
        var characteristic = this.characteristics[characteristicName];
        if (characteristic) {
            this.log("%s: set(%s, %s)", this.name, characteristicName, value);
            var url = this.deviceURL + "&cmd=setCharacteristic&" + characteristicName + "=" + String(value);
            this.indigoRequest(url, callback);
        }
        else {
            this.log("ERROR: %s: set for unknown characteristic %s", this.name, characteristicName);
            if (callback) {
                callback("Unknown characteristic " + characteristicName);
            }
        }
    }.bind(this);
};

// Returns the HomeKit services that this accessory supports
Indigo2Accessory.prototype.getServices = function() {
    return this.services;
};

// Updates the Accessory's characteristic values, notifying HomeKit of any changes
// characteristics: JSON array of characteristics from the Indigo RESTful API
Indigo2Accessory.prototype.updateCharacteristics = function(characteristics) {
    if (Array.isArray(characteristics)) {
        for (var characteristic in characteristics) {
            var name = characteristic.name;
            if (name) {
                var newValue = characteristic.value;
                var old = this.characteristics[name];
                var oldValue;
                if (old) {
                    oldValue = old.value;
                }
                this.characteristics[name] = characteristic;
                if (oldValue != newValue) {
                    var characteristicType = Characteristic[name];
                    if (characteristicType) {
                        var c = this.service.getCharacteristic(characteristicType);
                        if (c) {
                            this.log("%s: %s: %s -> %s", this.name, name, oldValue, newValue);
                            c.updateValue(newValue);
                        } else {
                            this.log("%s: ERROR: Unable to get Characteristic named %s", this.name, name);
                        }
                    }
                    else {
                        this.log("%s: ERROR: Unknown Characteristic name: %s", this.name, name);
                    }
                }
            }
        }
    }
};

// Calls the Indigo RESTful API to get the latest state for this Accessory, and updates the Accessory's properties to match
// callback: invokes callback(error), error is undefined if no error occurred
Indigo2Accessory.prototype.indigoRequest = function(url, callback) {
    this.platform.indigoRequestJSON(url, "GET", null,
        function(error, json) {
            if (error) {
                if (callback) {
                    callback(error);
                }
            }
            else if (Array.isArray(json.hkcharacteristics)) {
                this.updateCharacteristics(json.hkcharacteristics);
                if (callback) {
                    callback();
                }
            }
            else {
                if (callback) {
                    callback("Invalid response to request - missing hkcharacteristics")
                }
            }
        }.bind(this)
    );
};

// Calls the Indigo RESTful API to get the latest state of this Accessory, and updates the Accessory's properties to match,
// notifying HomeKit of any changes.
// callback: invokes callback(error), error is undefined if no error occurred
Indigo2Accessory.prototype.refresh = function(callback) {
    this.log("%s: refresh()", this.name);
    this.indigoRequest(this.deviceURL + "&cmd=getInfo", callback);
};

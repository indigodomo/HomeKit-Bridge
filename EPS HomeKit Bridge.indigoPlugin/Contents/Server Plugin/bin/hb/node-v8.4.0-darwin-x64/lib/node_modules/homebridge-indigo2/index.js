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
    "port": Port number of your HomeKit-Bridge RESTful API server (required)
    "serverId": Identifier of the HomeKit-Bridge server instance (required)
    "accessoryNamePrefix": Prefix all accessory names with this string (optional, useful for testing)
    "listenPort": homebridge-indigo2 will listen on this port for device state updates from HomeKit-Bridge (required)
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
            this.log("HomeKit-Bridge request: %s", options.url);
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
    this.log("HomeKit-Bridge base URL is %s", this.baseURL);

    if (config.serverId) {
        this.serverId = String(config.serverId);
        this.log("HomeKit-Bridge serverId is %s", this.serverId)
    } else {
        this.log("WARNING: serverId not configured");
    }

    if (config.accessoryNamePrefix) {
        this.accessoryNamePrefix = config.accessoryNamePrefix;
        this.log("Using accessory name prefix '%s'", this.accessoryNamePrefix)
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
            else {
                json.forEach(this.addAccessory.bind(this));
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

    var service = Service[String(serviceName)];
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

    var type = item.object;
    if (! type) {
        this.log("Error: Device %s has no object type", id);
        return null;
    }
    type = String(type);

    this.log("Discovered %s %s (ID %s): %s", type, serviceName, id, name);
    return new Indigo2Accessory(this, service, url, id, type, name, item);
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
function Indigo2Accessory(platform, serviceType, deviceURL, id, type, name, json) {
    this.platform = platform;
    this.log = platform.log;
    this.deviceURL = deviceURL;
    this.id = id;
    this.type = type;
    this.name = name;

    this.updateFromJSON(json);

    Accessory.call(this, this.name, uuid.generate(String(this.id)));

    this.infoService = this.getService(Service.AccessoryInformation);
    this.infoService.setCharacteristic(Characteristic.Manufacturer, "Indigo HomeKit-Bridge")
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
Indigo2Accessory.REFRESH_CONTEXT = 'refresh';


// Returns the HomeKit services that this accessory supports
Indigo2Accessory.prototype.getServices = function() {
    return this.services;
};

// Updates the Accessory's properties with values from JSON from the Indigo RESTful API
// json: JSON object from the Indigo RESTful API
// updateCallback: optional, invokes updateCallback(propertyName, propertyValue) for each property that has changed value
Indigo2Accessory.prototype.updateFromJSON = function(json, updateCallback) {
    for (var prop in json) {
        if (prop != "name" && prop != "id" && prop != "deviceURL" && prop != "type" && json.hasOwnProperty(prop)) {
            if (json[prop] != this[prop]) {
                this[prop] = json[prop];
                if (updateCallback) {
                    updateCallback(prop, json[prop]);
                }
            }
        }
    }
};

// Calls the Indigo RESTful API to get the latest state for this Accessory, and updates the Accessory's properties to match
// callback: invokes callback(error), error is undefined if no error occurred
// updateCallback: optional, invokes updateCallback(propertyName, propertyValue) for each property that has changed value
Indigo2Accessory.prototype.getStatus = function(callback, updateCallback) {
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
Indigo2Accessory.prototype.updateStatus = function(qs, callback, updateCallback) {
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
Indigo2Accessory.prototype.query = function(key, callback) {
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
Indigo2Accessory.prototype.updateProperty = function(prop, value) {
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
Indigo2Accessory.prototype.refresh = function(callback) {
    this.log("%s: refresh()", this.name);
    this.getStatus(callback, this.updateProperty.bind(this));
};

// Updates the Accessory's properties to match the provided JSON key/value pairs
// Invokes the Accessory's update_KEY function for each property KEY where the value has changed from the prior cached state
// If the Accessory does not have an update_KEY function for a given KEY, it is safely ignored
// This is used when we are listening on the listenPort for notifications from Indigo about devices that have changed state
// json: the JSON key/value pairs to update
Indigo2Accessory.prototype.refreshFromJSON = function(json) {
    this.log("%s: refreshFromJSON()", this.name);
    this.updateFromJSON(json, this.updateProperty.bind(this));
};

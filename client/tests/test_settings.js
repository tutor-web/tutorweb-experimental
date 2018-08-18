"use strict";
var test = require('tape');

var getSetting = require('../lib/settings.js').getSetting;

test('_getSetting', function (t) {
    // Get default values if nothing there
    t.equal(getSetting({}, 'parp', 'ping'), 'ping');
    t.equal(getSetting({}, 'parp', 0.4), 0.4);

    // Otherwise get set value
    t.equal(getSetting({'parp': 'poot'}, 'parp', 'ping'), 'poot');
    t.equal(getSetting({'parp': 0.8}, 'parp', 0.4), 0.8);

    // Non-float values are ignored
    t.equal(getSetting({'parp': 'poot'}, 'parp', 0.4), 0.4);

    t.end();
});

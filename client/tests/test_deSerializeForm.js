"use strict";
/*jslint nomen: true, plusplus: true*/
var test = require('tape');

var proto = '__proto__';

function NodeList() {
    var out = Array.apply(null, arguments);

    out[proto] = NodeList.prototype;
    return out;
}
NodeList.prototype = {};
NodeList.prototype[proto] = Array.prototype;
global.window = { NodeList: NodeList };

var formson = require('formson');

// NB: deSerializeForm used to be part of this project, replaced with formson
test('deSerializeForm', function (t) {
    // Build a fake form object, run deSerializeForm on it, return
    function do_dsf(element_names, data) {
        var fake_form = { elements: element_names.map(function (n) {
            return {nodeName: 'INPUT', type: 'text', name: n, value: "DEFAULT-" + n};
        })};

        fake_form.elements.forEach(function (el) {
            if (!fake_form.elements.hasOwnProperty(el.name)) {
                fake_form.elements[el.name] = el;
            } else if (fake_form.elements[el.name] instanceof global.window.NodeList) {
                fake_form.elements[el.name].push(el);
            } else {
                fake_form.elements[el.name] = new global.window.NodeList(fake_form.elements[el.name], el);
            }
        });

        formson.update_form(fake_form, data);
        return fake_form.elements.map(function (el) {
            return { name: el.name, value: el.value };
        });
    }

    t.deepEqual(do_dsf([], {}), [], "No elements or data passes through");
    t.deepEqual(do_dsf([], { parp: "yes" }), [], "Just data passes through");

    t.deepEqual(do_dsf(['parp', 'peep'], {
        parp: "yes",
        peep: "maybe",
    }), [
        { name: "parp", value: "yes" },
        { name: "peep", value: "maybe" },
    ], "Set fields");

    t.deepEqual(do_dsf(['parp', 'peep'], {
        parp: "yes",
    }), [
        { name: "parp", value: "yes" },
        { name: "peep", value: "DEFAULT-peep" },
    ], "Set fields, leave values we don't have data for alone");

    t.deepEqual(do_dsf(['parp', 'pigs[]', 'cows[]', 'cows[]', 'cows[]', 'pigs[]'], {
        parp: "yes",
        peep: "maybe",
        cows: ['freda', 'bessie', 'spider', 'blob'],
        pigs: ['george', 'wilma'],
    }), [
        { name: "parp", value: "yes" },
        { name: "pigs[]", value: "george" },
        { name: "cows[]", value: "freda" },
        { name: "cows[]", value: "bessie" },
        { name: "cows[]", value: "spider" },
        { name: "pigs[]", value: "wilma" },  // NB: Ordering didn't faze us
    ], "Can dereference arrays");

    t.deepEqual(do_dsf(['cows[]', 'cows[]', 'cows[]'], {
        cows: ['freda'],
    }), [
        { name: "cows[]", value: "freda" },
        { name: "cows[]", value: "" },
        { name: "cows[]", value: "" },
    ], "If we run out of array elements, clear elements");

    t.end();
});

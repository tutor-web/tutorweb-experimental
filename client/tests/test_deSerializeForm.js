"use strict";
/*jslint nomen: true, plusplus: true*/
var test = require('tape');

var deSerializeForm = require('lib/deSerializeForm.js').deSerializeForm;

test('deSerializeForm', function (t) {
    // Build a fake form object, run deSerializeForm on it, return
    function do_dsf(element_names, data) {
        var fake_form = { elements: element_names.map(function (n) {
            return {name: n, value: "DEFAULT-" + n};
        })};

        deSerializeForm(fake_form, data);
        return fake_form.elements;
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
        { name: "cows[]", value: "DEFAULT-cows[]" },
        { name: "cows[]", value: "DEFAULT-cows[]" },
    ], "If we run out of array elements, leave alone");

    t.end();
});


/*jslint nomen: true, plusplus: true, browser:true, regexp: true, unparam: true, todo: true */
/*global require, Promise */
"use strict";

module.exports.deSerializeForm = function (form_el, data) {
    var counts = {};

    Array.prototype.map.call(form_el.elements, function (el) {
        var base_name;

        if (el.name.indexOf('[]') > -1) {
            base_name = el.name.replace(/\[\]$/, '');
            if (!counts[base_name]) {
                counts[base_name] = 0;
            }
            if (data[base_name].length > counts[base_name]) {
                el.value = data[base_name][counts[base_name]++];
            }
        } else if (data.hasOwnProperty(el.name)) {
            el.value = data[el.name];
        }
    });
};

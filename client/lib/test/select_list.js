"use strict";
/*jslint nomen: true, plusplus: true, browser:true, todo: true */
/*global require */

var h = require('hyperscript');
var jQuery = require('jquery');
var select_list = require('lib/select_list.js').select_list;

function renderLink (data) {
    if (data.ignore) {
        return null;
    }
    return h('a', { href: '#' }, [data.title]);
}

jQuery(document.getElementById('tw-quiz')).append([
    select_list([
        {title: "Cows", children: [
            {title: "Daisy", children: [
                {title: "Legs: 4"},
                {title: "Noise: moo"},
            ]},
            {title: "Freda"},
            {title: "Fessie", children: [
                {title: "Legs: 666"},
                {title: "Noise: brawk"},
            ], ignore: true},
            {title: "Bessie", children: [
                {title: "Legs: 4"},
                {title: "Noise: moo"},
            ]},
        ]},
        {title: "Pigs", children: [
            {title: "George"},
            {title: "Frank"},
        ]},
    ], renderLink, function (items) {
        console.log(items.map(function (d) { return d.title; }));
    })
]);

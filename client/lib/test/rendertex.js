"use strict";
/*jslint nomen: true, plusplus: true, browser:true, todo: true */
/*global require */
var jQuery = require('jquery');
var renderTex = require('lib/rendertex.js').renderTex;

Promise.all(Array.prototype.map.call(document.querySelectorAll('.rendertex-test'), function (el) {
    console.log(el);
    return renderTex(jQuery, jQuery(el));
}));

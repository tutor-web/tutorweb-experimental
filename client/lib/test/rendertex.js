"use strict";
/*jslint nomen: true, plusplus: true, browser:true, todo: true */
/*global require */
var jQuery = require('jquery');
var renderTex = require('lib/rendertex.js').renderTex;

window.run_tests = function () {
    return Promise.all(Array.prototype.map.call(document.querySelectorAll('.rendertex-test'), function (el) {
        console.log(el);
        return renderTex(jQuery, jQuery(el));
    }));
}

// Run tests twice to make sure we don't break already-rendered elements
window.run_tests().then(function () {
    setTimeout(window.run_tests, 1000);
});

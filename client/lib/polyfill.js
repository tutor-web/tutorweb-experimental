"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true */
/*global Promise, Element */
require('es6-promise').polyfill();
require('whatwg-fetch');
require('custom-event-polyfill');

// https://developer.mozilla.org/en-US/docs/Web/API/Element/matches
if (!Element.prototype.matches) {
    Element.prototype.matches = Element.prototype.msMatchesSelector;
}

require('ie-array-find-polyfill');

// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/isInteger
Number.isInteger = Number.isInteger || function (value) {
    return typeof value === 'number' &&
        isFinite(value) &&
        Math.floor(value) === value;
};

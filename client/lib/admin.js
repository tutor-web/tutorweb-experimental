"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true */
/*global Promise */
var parse_qs = require('lib/parse_qs.js').parse_qs;
var View = require('lib/view.js');
var Handsontable = require('handsontable');
var jQuery = require('jquery');
var AjaxApi = require('lib/ajaxapi.js');

function page_load(qs, state) {
    var ajaxApi = new AjaxApi(jQuery.ajax);

    Array.prototype.forEach.call(document.querySelectorAll('#csv-links a'), function (a_el) {
        a_el.href = a_el.href + '?path=' + qs.path;
    });

    return ajaxApi.getJson('/api/syllabus/student_grades?path=' + qs.path).then(function (data) {
        var headers, hot, hot_el = document.getElementById('results-hot');

        headers = data.results.shift();
        hot = new Handsontable(hot_el, {
            stretchH: 'all',
            autoWrapRow: true,
            colHeaders: headers,
            data: data.results,
        });
        window.hot = hot;
    });
}

function global_catch(err) {
    var twView = new View(jQuery);

    if (err.message.indexOf('tutorweb::unauth::') === 0) {
        // TODO: "Not an admin" caught by this too
        // i.e. do go-login
        window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname + window.location.search);
    }
    console.error(err);
    twView.showAlert('error', err.message);
}

if (window) {
    document.addEventListener('DOMContentLoaded', function (e) {
        page_load(parse_qs(window.location), window.history.state || {}).catch(global_catch);
    });
}

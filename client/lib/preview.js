"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true */
/*global Promise */
var formson = require('formson');
var jQuery = require('jquery');
var View = require('lib/view.js');
var renderTex = require('lib/rendertex.js').renderTex;
var AjaxApi = require('lib/ajaxapi.js');
var parse_qs = require('lib/parse_qs.js').parse_qs;

function page_load(e) {
    var twView = new View(jQuery),
        ajaxApi = new AjaxApi(jQuery.ajax),
        qs = parse_qs(window.location);

    formson.update_form(document.forms.preview_select, qs);
    if (!qs.path) {
        return;
    }

    return ajaxApi.getJson('/api/material/render?path=' + encodeURIComponent(qs.path) + '&permutation=' + encodeURIComponent(qs.permutation || 1)).then(function (material) {
        twView.jqQuiz.html(material.content);

        // Replace placeholders with the real content
        Array.prototype.map.call(twView.jqQuiz[0].querySelectorAll('div.reveal-on-answer-placeholder'), function (el) {
            el.parentNode.replaceChild(jQuery(el).data('orig'), el);
        });

        twView.renderMath();
    }).then(function () {
        twView.jqQuiz.removeClass('busy');
    }).catch(function (err) {
        twView.showAlert('error', err.message);
    });
}

if (window) {
    document.addEventListener('DOMContentLoaded', page_load);
}

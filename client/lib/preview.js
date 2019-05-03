"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true */
/*global Promise */
var formson = require('formson');
var jQuery = require('jquery');
var View = require('lib/view.js');
var renderTex = require('lib/rendertex.js').renderTex;
var AjaxApi = require('lib/ajaxapi.js');
var parse_qs = require('lib/parse_qs.js').parse_qs;
var Hodataframe = require('hodf');

var hodfs = {};

function page_load(qs, student_dataframes) {
    var twView = new View(jQuery),
        ajaxApi = new AjaxApi(jQuery.ajax);

    formson.update_form(document.forms.preview_select, qs);
    if (!qs.path) {
        // Nothing to do, don't bother doing it.
        return;
    }

    qs.student_dataframes = student_dataframes;
    return ajaxApi.postJson('/api/material/render', qs).then(function (data) {
        var dataframe_container_el = document.getElementById('dataframe-container');

        Object.keys(data.dataframe_templates || {}).forEach(function (k) {
            var el = document.createElement("div"), t;

            if (hodfs[k]) {
                hodfs[k] = hodfs[k].replace(student_dataframes[k]);
            } else {
                dataframe_container_el.appendChild(el);
                t = data.dataframe_templates[k];
                t.name = k;
                hodfs[k] = new Hodataframe(t, el, student_dataframes[k]);
            }
        });

        if (!data.content && data.error) {
            twView.showAlert('error', data.error);
            return;
        }
        twView.jqQuiz.html(data.content);

        // Replace placeholders with the real content
        Array.prototype.map.call(twView.jqQuiz[0].querySelectorAll('div.reveal-on-answer-placeholder'), function (el) {
            el.parentNode.replaceChild(jQuery(el).data('orig'), el);
        });

        twView.renderMath();
    }).then(function () {
        twView.jqQuiz.removeClass('busy');
    }).catch(function (err) {
        console.error(err);
        twView.showAlert('error', err.message);
    });
}

if (window) {
    document.addEventListener('DOMContentLoaded', function (e) {
        page_load(parse_qs(window.location), window.history.state || {});
    });

    window.addEventListener('popstate', function (e) {
        page_load(parse_qs(window.location), window.history.state || {});
    });

    document.forms.preview_select.addEventListener('submit', function (e) {
        var form_data, student_dataframes = {};

        e.preventDefault();
        e.stopPropagation();

        // Read form, adding in hodf data
        form_data = formson.form_to_object(e.target);
        Object.values(hodfs).forEach(function (hodf) {
            student_dataframes[hodf.name] = hodf.getDataFrame();
        });

        // Update form, add state to browser history
        page_load(form_data, student_dataframes);
        history.pushState(student_dataframes, "", '/preview.html?path=' + encodeURIComponent(form_data.path) + '&permutation=' + encodeURIComponent(form_data.permutation));
    });
}

/*jslint nomen: true, plusplus: true, browser:true, regexp: true, todo: true */
/*global module, Promise */
"use strict";
var jQuery = require('jquery');
var render_progress = require('lib/progress.js').render_progress;

module.exports['data-display'] = function () {
    render_progress(this.jqQuiz, 10, 100, "Fetching data frames");

    return window.fetch('/api/stage/dataframe?path=' + encodeURIComponent(this.curUrl.path), {
        method: "GET",
    }).then(function (response) {
        return response.json();
    }.bind(this)).then(function (data) {
        var Hodataframe = require('hodf');

        this.jqQuiz[0].innerHTML = '';
        if (this.lastError) {
            this.showAlert('error', this.lastError, 'html');
        }

        this.selected_item = Object.keys(data).map(function (k) {
            var el = document.createElement("div"), t;
            this.jqQuiz[0].appendChild(el);

            t = data[k].template;
            t.name = k;
            return new Hodataframe(t, el, data[k].data);
        }.bind(this));
        this.updateActions(['reload', 'data-save']);
    }.bind(this));
};

module.exports['data-save'] = function () {
    var data = {};

    this.selected_item.map(function (hodf) {
        var d = hodf.getDataFrame(), name = hodf.name;
        hodf.hot.destroy();  // TODO: Make a helper for this
        data[name] = d;
    });

    return window.fetch('/api/stage/dataframe?path=' + encodeURIComponent(this.curUrl.path), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            data: data,
        }),
    }).then(function (response) {
        if (response.status !== 200) {
            throw new Error(response);
        }
        return response.json();
    }.bind(this)).then(function () {
        return this.quiz.syncLecture(this.quiz.lecUri, {
            ifMissing: 'fetch',
            syncForce: true,
            skipQuestions: false,
            forceQuestions: true,
            skipCleanup: false,
        }, function (opTotal, opSucceeded, message) {
            render_progress(this.jqQuiz, opSucceeded, opTotal, message);
        }.bind(this));
    }.bind(this)).then(function () {
        window.location.reload();
    }.bind(this));
};

module.exports.extend = function (twView) {
    twView.states['data-display'] = module.exports['data-display'];
    twView.states['data-save'] = module.exports['data-save'];

    twView.locale['data-display'] = "View/Update stage data";
    twView.locale['data-save'] = "Save stage data";
};

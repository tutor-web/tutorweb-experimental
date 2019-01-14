/*jslint nomen: true, plusplus: true, browser:true, regexp: true, todo: true */
/*global module, Promise */
"use strict";
var jQuery = require('jquery');

function el(name) {
    return jQuery(document.createElement(name));
}

/** Render a progress bar in the box */
module.exports.render_progress = function (jqQuiz, count, max, message) {
    var jqBar = jqQuiz.find('div.progress div.bar'),
        perc;
    if (!jqBar.length && count === 'increment') {
        throw new Error("Need existing bar to increment count");
    }

    if (jqBar.length) {
        perc = count === 'increment' ? parseInt(jqBar[0].style.width, 10) + Math.round((1 / max) * 100)
                                     : Math.round((count / max) * 100);
        jqBar.css({"width": perc + '%'});
        jqQuiz.find('p.message').text(message);
    } else {
        perc = Math.round((count / max) * 100);
        jqQuiz.empty().append([
            el('p').attr('class', 'message').text(message),
            el('div').attr('class', 'progress').append(el('div').attr('class', 'bar').css({"width": perc + '%'})),
            null
        ]);
    }
};

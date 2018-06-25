"use strict";
/*jslint nomen: true, plusplus: true, browser:true, todo: true */
/*global require */
var jQuery = require('jquery');
var Quiz = require('./quizlib.js');
var View = require('./view.js');
var AjaxApi = require('./ajaxapi.js');
var UserMenu = require('./usermenu.js');
var parse_qs = require('../lib/parse_qs.js').parse_qs;
var isQuotaExceededError = require('./ls_utils.js').isQuotaExceededError;
var h = require('hyperscript');
var select_list = require('lib/select_list.js').select_list;

function StartView() {
    /** Generate expanding list for tutorials / lectures */
    this.renderChooseLecture = function (subscriptions) {
        this.jqQuiz.empty().append(h('div', [
            h('h2', 'Your lectures'),
            select_list(subscriptions.subscriptions.children, function (data) {
                return h('a', {
                    href: data.href ? '/stage?path=' + encodeURIComponent(data.href) : '#',
                }, [
                    data.title,
                    h('span.grade', data.grade),
                ]);
            }),
        ]));
    };
}
StartView.prototype = new View(jQuery);

(function (window, $) {
    var quiz, twView, twMenu,
        unsyncedLectures = [];

    // Do nothing if not on the right page
    if (!window) { return; }

    // Wire up quiz object
    twView = new StartView($);

    // Start state machine
    twView.locale.logout = 'Clear data and logout';

    // Create Quiz model
    twView.states.initial = function () {
        quiz = new Quiz(localStorage, new AjaxApi($.ajax));
        twMenu = new UserMenu($('#tw-usermenu'), quiz);
        twMenu.noop = 1; // NB: Keep JSLint quiet
        twView.updateActions(['logout', '']);
        return 'subscription-sync';
    };

    twView.states['subscription-sync'] = twView.states['subscription-remove'] = twView.states['subscription-sync-force'] = function (curState) {
        return quiz.syncSubscriptions({
            syncForce: curState === 'subscription-sync-force',
            lectureDel: curState === 'subscription-remove' ? parse_qs({hash: twView.selectListHref()}).lecUri  : null,
        }, function (opTotal, opSucceeded, message) {
            twView.renderProgress(opSucceeded, opTotal, message);
        }).then(function () {
            return 'lecturemenu';
        })['catch'](function (err) {
            if (isQuotaExceededError(err)) {
                return 'menu-cleanstorage';
            }
            if (err.message.indexOf('tutorweb::unauth::') === 0) {
                return 'go-login';
            }
            if (err.message.indexOf('tutorweb::neterror::') === 0) {
                // i.e. we're probably offline
                return 'lecturemenu';
                //TODO: But what if we didn't manage to get the subscriptions table? Empty isn't good enough.
            }
            if (err.message.indexOf('tutorweb::') !== -1) {
                var parts = err.message.split(/\:\:/).splice(1);
                twView.showAlert(parts[0], 'Syncing failed: ' + parts[1], parts[2]);
            } else {
                twView.showAlert('error', 'Syncing failed: ' + err.message);
            }
            // Stop and give user a chance to reconsider
            twView.updateActions(['reload', 'lecturemenu']);
        });
    };

    twView.states['menu-cleanstorage'] = function () {
        return quiz.getAvailableLectures().then(function (subscriptions) {
            twView.renderChooseLecture(
                subscriptions,
                [],
                ['subscription-remove']
            );
            twView.showAlert('warning', 'You have run out of storage space. Please choose items to remove.');
        });
    };

    twView.states.lecturemenu = function () {
        return quiz.getAvailableLectures().then(function (subscriptions) {
            if (Object.keys(subscriptions.lectures).length === 0) {
                twView.jqQuiz.empty();
                twView.showAlert('info', 'You have no lectures loaded yet. Please click "Get more drill questions", and choose a department and tutorial from which you would like to learn.');
                twView.updateActions(['logout', 'go-twhome']);
            } else {
                twView.renderChooseLecture(
                    subscriptions,
                    ['go-twhome', ''],
                    ['go-twhome', 'subscription-remove', 'go-slides', 'go-drill']
                );
            }

            // Get all lecture titles from unsynced lectures
            unsyncedLectures = Object.keys(subscriptions.lectures)
                .filter(function (k) { return !subscriptions.lectures[k].synced; })
                .map(function (k) { return subscriptions.lectures[k].title; });
        });
    };

    twView.states.logout = function () {
        if (unsyncedLectures.length === 0 || window.confirm("Your answers to " + unsyncedLectures[0] + " haven't been sent to the Tutor-Web server.\nIf you click okay some answers will be lost")) {
            localStorage.clear();
            window.location.href = twView.portalRootUrl('logout');
        }
    };

    twView.states['go-slides'] = function () {
        window.location.href = 'slide.html' + twView.selectListHref();
    };

    twView.states['go-drill'] = function () {
        window.location.href = 'quiz.html' + twView.selectListHref();
    };

    twView.stateMachine();
}(window, jQuery));

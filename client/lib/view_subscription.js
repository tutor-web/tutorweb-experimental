/*jslint nomen: true, plusplus: true, browser:true, regexp: true, todo: true */
/*global module, Promise */
"use strict";
var AjaxApi = require('lib/ajaxapi.js');
var select_list = require('lib/select_list.js').select_list;
var h = require('hyperscript');
var jQuery = require('jquery');

var ajaxApi = new AjaxApi(jQuery.ajax);

module.exports['subscription-menu'] = function () {
    var self = this;

    return ajaxApi.postJson('/api/subscriptions/available').then(function (sub_data) {
        self.jqQuiz.empty().append([
            h('h2', 'Tutorials you can subscribe to'),
            select_list(sub_data.children, function (data) {
                var link_el = null;

                if (data.supporting_material_href) {
                    link_el = h('a.link.pdf', {
                        href: data.supporting_material_href,
                        title: 'Download notes',
                        target: '_blank',
                    }, [
                        h('img', {src: '/images/page_white_put.png'}),
                    ]);
                }

                return h('a', { href: '#' }, [
                    data.title,
                    h('div.extras', [
                        link_el,
                        data.subscribed ? h('span.correct', "✔") : '',
                    ]),
                ]);
            }, function (selected_items) {
                var final_item;

                if (selected_items.length === 0) {
                    self.updateActions(['gohome', '']);
                    return;
                }

                final_item = selected_items[selected_items.length - 1];
                if (final_item.subscribed) {
                    self.selected_item = final_item.subscribed;
                    self.updateActions(['gohome', 'subscription-remove']);
                } else {
                    self.selected_item = final_item.path;
                    self.updateActions(['gohome', 'subscription-add']);
                }
            }),
        ]);
    });
};

module.exports['subscription-add'] = module.exports['subscription-remove'] = function (curState) {
    var self = this,
        endpoint = curState === 'subscription-add' ? 'add' : 'remove';

    self.updateActions([]);
    return ajaxApi.postJson('/api/subscriptions/' + endpoint + '?path=' + encodeURIComponent(self.selected_item)).then(function () {
        return self.quiz.syncSubscriptions({}, function (opTotal, opSucceeded, message) {
            self.renderProgress(opSucceeded, opTotal, message);
        }).then(function () {
            return 'subscription-menu';
        });
    });
};

module.exports.extend = function (twView) {
    Object.keys(module.exports).map(function (name) {
        if (name !== 'extend') {
            twView.states[name] = module.exports[name];
        }
    });

    twView.locale['subscription-menu'] = "Get more tutorials";
    twView.locale['subscription-remove'] = "Unsubscribe from this tutorial";
    twView.locale['subscription-add'] = "Subscribe to this tutorial";
};

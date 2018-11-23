/*jslint nomen: true, plusplus: true, browser:true, regexp: true, todo: true */
/*global module, Promise */
"use strict";
var h = require('hyperscript');
var select_list = require('lib/select_list.js').select_list;

function renderReview(twView, reviewData) {
    twView.jqQuiz.empty().append([
        h('h3', 'Material you have written'),
        (reviewData.material.length === 0 ? h('p', "You haven't written anything yet") : null),
    ]);
    twView.jqQuiz.append(select_list(reviewData.material, function (data) {
        var extras_el, content_el;

        if (data.uri) {
            if (!data.text) {
                // Ignore anything that has no text
                return null;
            }
            content_el = h('pre.parse-as-rst', data.text);
        } else {
            // Comments are already rendered as HTML when we get them
            content_el = h('div');
            content_el.innerHTML = data.comments || '<p>(reviewed without comment)</p>';
        }

        if (data.correct !== undefined) {
            extras_el = h('div.extras', [h('abbr', { title: data.mark }, [
                data.correct === true ? h('span.correct', "✔") : data.correct === false ? h('span.incorrect', "✗") : '-',
            ])]);
        } else {
            extras_el = h('div.extras', [h('span', data.mark)]);
        }

        return h('a', {
        }, [
            extras_el,
            content_el,
        ]);
    }, function (items) {
        if (items.length > 0) {
            twView.selected_item = items[0];
            twView.updateActions(['gohome', 'ug-review-material', 'ug-rewrite', 'ug-write']);
        } else {
            twView.selected_item = null;
            twView.updateActions(['gohome', 'ug-review-material', 'ug-write']);
        }
    }));
    twView.renderMath();
}

module.exports['ug-review'] = function () {
    this.updateActions([]);

    return this.quiz.syncLecture(this.curUrl.lecUri, {
        // Always sync first so we pick up new reviews
        syncForce: true,
    }).then(function () {
        return this.quiz.fetchReview(this.curUrl.lecUri);
    }.bind(this)).then(function (review) {
        renderReview(this, review);
    }.bind(this));
};

module.exports['ug-review-material'] = function () {
    this.updateActions([]);
    return this.quiz.getReviewMaterial().then(function (material_found) {
        if (material_found) {
            return 'quiz-real';
        }
        this.showAlert('info', 'There is nothing more ready for review');
        this.updateActions(['gohome', 'ug-review-material', 'ug-write']);
    }.bind(this));
};

module.exports['ug-write'] = module.exports['ug-rewrite'] = function (curState) {
    this.updateActions([]);
    return (curState === 'ug-write' ? this.quiz.getNewQuestion({}) : this.quiz.rewriteUgMaterial(this.selected_item)).then(function (args) {
        args.actions = ['qn-skip', 'qn-submit'];

        this.quiz.lectureGradeSummary(this.curUrl.lecUri).then(this.renderGradeSummary.bind(this));
        return this.renderNewQuestion(args.qn, args.a, args.actions).then(function () {
            return args;
        });
    }.bind(this)).then(function (args) {
        var skipAction = args.actions[0];
        this.updateActions([skipAction]);
        this.twTimer.reset();
    }.bind(this));
};

module.exports.extend = function (twView) {
    Object.keys(module.exports).map(function (name) {
        if (name !== 'extend') {
            twView.states[name] = module.exports[name];
        }
    });

    twView.locale['ug-review'] = "Review material written by you";
    twView.locale['ug-review-material'] = "Review material written by others";
    twView.locale['ug-write'] = "Write new material";
    twView.locale['ug-rewrite'] = "Remove this material and rewrite it";
};

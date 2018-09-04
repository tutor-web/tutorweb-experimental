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

        if (!(data.text || data.comments)) {
            return null;
        }
        content_el = h('pre.parse-as-rst', (data.text || data.comments));

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
        this.updateActions(['gohome', 'ug-review-material', 'ug-write']);
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

module.exports['ug-write'] = function (curState) {
    this.updateActions([]);
    return this.quiz.getNewQuestion({
        question_uri: curState === 'rewrite-question' ? this.selectedQn : null,
    }).then(function (args) {
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
    twView.locale['ug-rerewrite'] = "Rewrite this question";
};

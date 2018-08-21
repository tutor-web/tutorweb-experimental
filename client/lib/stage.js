/*jslint nomen: true, plusplus: true, browser:true, regexp: true, unparam: true, todo: true */
/*global require, Promise */
var jQuery = require('jquery');
require('es6-promise').polyfill();
var Quiz = require('lib/quizlib.js');
var View = require('lib/view.js');
var AjaxApi = require('lib/ajaxapi.js');
var Timer = require('lib/timer.js');
var UserMenu = require('lib/usermenu.js');
var serializeForm = require('@f/serialize-form');
var h = require('hyperscript');

/**
  * View class to translate data into DOM structures
  *    $: jQuery
  */
function QuizView($) {
    "use strict";
    this.jqDebugMessage = $('#tw-debugmessage');
    this.jqGrade = $('#tw-grade');
    this.jqAnswers = $('#tw-answers');
    this.ugQnRatings = [
        [100, "Very hard"],
        [75, "Hard"],
        [50, "Good"],
        [25, "Easy"],
        [0, "Too easy"],
        [-1, "Doesn't make sense"],
        [-2, "Superseded"],
    ];

    // Generate a jQueried DOM element
    function el(name) {
        return $(document.createElement(name));
    }

    /** Update the debug message with current URI and an extra string */
    this.updateDebugMessage = function (lecUri, qn) {
        var self = this;
        if (lecUri) { self.jqDebugMessage[0].lecUri = lecUri; }
        self.jqDebugMessage.text(self.jqDebugMessage[0].lecUri + "\n" + qn);
    };

    /** Render next question */
    this.renderNewQuestion = function (qn, a, actionsOnChange) {
        var self = this, jqForm = el('form');

        self.updateDebugMessage(null, a.uri.replace(/.*\//, ''));
        jqForm.append(self.renderQuestion(qn, a));

        jqForm.on('change', function () {
            self.updateActions(actionsOnChange);
        });
        jqForm.on('keypress', function () {
            // Typing in a textarea should also change actions
            self.updateActions(actionsOnChange);
        });

        self.jqQuiz.empty().append([
            qn._type === 'usergenerated' ? el('div').attr('class', 'usergenerated alert alert-info').text('This question is written by a fellow student. Your answer to this question will not count towards your grade.') : null,
            jqForm,
        ]);
        return self.renderMath();
    };

    /** Annotate with correct / incorrect selections */
    this.renderAnswer = function (a, answerData) {
        var self = this,
            parsedExplanation = $(jQuery.parseHTML(answerData.explanation));
        self.jqQuiz.find('input,textarea').attr('disabled', 'disabled');

        // If text in explanation is equivalent to nothing, then don't put anything out
        if ($.trim(parsedExplanation.text()) === "") {
            parsedExplanation = null;
        }

        if (a.question_type === 'template') {
            // No marking to do, just show a thankyou message
            parsedExplanation = parsedExplanation || (a.student_answer && a.student_answer.text ?
                                     'Thankyou for submitting a question' :
                                     'Your question has not been saved');
            self.jqQuiz.append(el('div').attr('class', 'alert explanation').html(parsedExplanation));
            self.renderMath();

        } else if (a.question_type === 'usergenerated' && a.student_answer.hasOwnProperty('comments')) {
            // Rated the question as well as answered it, just say thankyou
            self.jqQuiz.find('div.alert.usergenerated').remove();
            self.jqQuiz.append(el('div').attr('class', 'alert alert-info').text("Thank you for trying this question!"));

        } else {
            self.jqQuiz.find('#answer_' + a.selected_answer).addClass('selected');
            // Mark all answers as correct / incorrect
            Object.keys(answerData).map(function (k) {
                if (Array.isArray(answerData[k])) {
                    // Find any form elements with key/value and mark as correct
                    self.jqQuiz.find('*[name=' + k + ']').each(function () {
                        var correct = answerData[k].indexOf($(this).val()) > -1;
                        this.classList.toggle('correct', correct);
                        this.classList.toggle('incorrect', !correct);
                    });
                }
            });

            if (a.hasOwnProperty('correct')) {
                self.jqQuiz.children('form').toggleClass('correct', a.correct);
                self.jqQuiz.children('form').toggleClass('incorrect', !a.correct);
            }

            if (parsedExplanation) {
                self.jqQuiz.children('form').append(el('div').attr('class', 'alert explanation').html(parsedExplanation));
                self.renderMath();
            }
        }
    };

    /** Add on form to speak your branes */
    this.renderReviewForm = function () {
        this.jqQuiz.append(el('form').append([
            el('label').text("How did you find the question?"),
            el('ol').append(this.ugQnRatings.map(function (rating) {
                if (rating[0] < -1) {
                    // Can't select superseded
                    return null;
                }
                return el('li').append([
                    el('label').text(rating[1]).prepend([
                        el('input').attr('type', 'radio').attr('name', 'rating').attr('value', rating[0])
                    ])
                ]);
            })),
            el('label').text("Any other comments?"),
            el('textarea').attr('name', 'comments')
        ]));
    };

    this.renderGradeSummary = function (summary) {
        var self = this,
            jqGrade = self.jqGrade,
            jqStats = this.jqAnswers.find('.current'),
            jqList = this.jqAnswers.children('ol.previous');

        jqGrade.text(summary.practice || summary.grade || '');
        if (summary.encouragement) {
            jqGrade.text(jqGrade.text() + ' ~ ' + summary.encouragement);
        }
        jqStats.text(summary.practiceStats || summary.stats || '');
        jqList.empty().append((summary.lastEight || []).map(function (a) {
            var t = new Date(0),
                title = '';
            t.setUTCSeconds(a.time_end);

            if (a.selected_answer) {
                title += 'You chose ' + String.fromCharCode(97 + a.selected_answer) + '\n';
            }
            title += 'Answered ' + t.toLocaleDateString() + ' ' + t.toLocaleTimeString();

            if (a.correct === true) {
                return $('<li/>').attr('title', title)
                                 .addClass('correct')
                                 .append($('<span/>').text("✔"));
            }
            if (a.correct === false) {
                return $('<li/>').attr('title', title)
                                 .addClass('incorrect')
                                 .append($('<span/>').text("✗"));
            }
            return $('<li/>').attr('title', title).append($('<span/>').text("-"));
        }));
    };

    this.renderStart = function (args) {
        var self = this;
        $("#tw-title").text(args.lecTitle);
        self.jqQuiz.empty().append($("<p/>").text(
            args.continuing ? "Click 'Continue question' to carry on" : "Click 'New question' to start"
        ));
        self.updateDebugMessage(args.lecUri, '');
    };

}
QuizView.prototype = new View(jQuery);

(function (window, $) {
    "use strict";
    var quiz, twView, twTimer, twMenu;
    // Do nothing if not on the right page
    if (!window) { return; }

    // Make instructions box toggle open
    $(".instructions_box").hide();
    $('.instructions_heading').click(function () {
        $('.instructions_box').toggle();
    });

    // Wire up Quiz View
    twView = new QuizView($);
    twTimer = new Timer($('#tw-timer span'));
    twView.twTimer = twTimer;

    // Create Quiz model
    twView.states.initial = function () {
        quiz = new Quiz(localStorage, new AjaxApi($.ajax));
        twView.quiz = quiz;
        twMenu = new UserMenu($('#tw-usermenu'), quiz);
        return 'set-lecture';
    };

    // Load the lecture referenced in URL, if successful hit the button to get first question.
    twView.states['set-lecture'] = function () {
        twView.updateActions([]);
        return quiz.setCurrentLecture({lecUri: twView.curUrl.path}).then(function (args) {
            twView.renderStart(args);
            quiz.lectureGradeSummary(twView.curUrl.lecUri).then(twView.renderGradeSummary.bind(twView));
            if (args.material_tags.indexOf("type.template") > -1) {
                twView.postQuestionActions = ['ug-review', 'ug-review-material', 'ug-write'];
                return 'ug-review';
            }
            if (args.material_tags.indexOf("type.example") > -1) {
                twView.postQuestionActions = ['gohome', 'load-example'];
                return 'quiz-real';
            }
            twView.postQuestionActions = ['gohome', 'quiz-practice', 'quiz-real'];
            if (args.continuing === 'practice') {
                return 'quiz-practice';
            }
            if (args.continuing === 'real') {
                return 'quiz-real';
            }
            twView.updateActions(['gohome', (args.practiceAllowed > 0 ? 'quiz-practice' : null), 'quiz-real']);
        })['catch'](function (err) {
            if (err.message.indexOf("Unknown lecture: ") === 0) {
                twView.showAlert('info', 'You are not subscribed yet, you need to subscribe before taking drills. Do you wish to?');
                twView.updateActions(['subscription-add']);
                return;
            }

            if (err.message.indexOf("Subscriptions not yet downloaded") === 0) {
                twView.updateActions([]);
                return quiz.syncSubscriptions({}, function (opTotal, opSucceeded, message) {
                    twView.renderProgress(opSucceeded, opTotal, message);
                }).then(function () {
                    return 'set-lecture';
                });
            }

            throw err;
        })['catch'](function (err) {
            if (err.message.indexOf('tutorweb::unauth::') === 0) {
                return 'go-login';
            }
        });
    };

    twView.states['subscription-add'] = function () {
        twView.updateActions([]);
        return quiz.syncSubscriptions({ lectureAdd:  twView.curUrl.lecUri }, function (opTotal, opSucceeded, message) {
            twView.renderProgress(opSucceeded, opTotal, message);
        }).then(function () {
            return 'set-lecture';
        });
    };

    twView.states['load-example'] = twView.states['quiz-real'] = twView.states['quiz-practice'] = function (curState, updateState) {
        twView.updateActions([]);
        return quiz.getNewQuestion({
            practice: curState.endsWith('-practice')
        }).then(function (args) {
            args.actions = ['qn-skip', 'qn-submit'];

            quiz.lectureGradeSummary(twView.curUrl.lecUri).then(twView.renderGradeSummary.bind(twView));
            return twView.renderNewQuestion(args.qn, args.a, args.actions).then(function () {
                return args;
            });
        }).then(function (args) {
            var skipAction = args.actions[0];

            if (args.qn.tags.indexOf("type.example") > -1) {
                // If it's an example, don't wait for an answer
                return 'qn-skip';
            }

            twView.updateActions([skipAction]);
            // Once MathJax is finished, start the timer
            if (args.a.remaining_time) {
                twTimer.start(function () {
                    twTimer.text("Out of time!");
                    updateState(skipAction);
                }, args.a.remaining_time);
            } else {
                twTimer.reset();
            }
        });
    };

    twView.states['qn-skip'] = twView.states['qn-submit'] = function (curState) {
        // Disable all controls and mark answer
        twView.updateActions([]);
        return quiz.setQuestionAnswer(curState.endsWith('-skip') ? {} : serializeForm(twView.jqQuiz.children('form')[0])).then(function (args) {
            var actions = twView.postQuestionActions;
            if (args.practiceAllowed > 0) {
                actions = twView.postQuestionActions.filter(function (a) { return a !== 'quiz-practice'; });
            }

            twView.renderAnswer(args.a, args.answerData, args.qn);
            quiz.lectureGradeSummary(twView.curUrl.lecUri).then(twView.renderGradeSummary.bind(twView));
            twMenu.syncAttempt(false);

            if (args.qn.tags.indexOf("review.mandatory") > -1) {
                return 'qn-startreview';
            }

            twView.updateActions([]);
            if (args.a.explanation_delay) {
                twTimer.start(function () {
                    twTimer.reset();
                    twView.updateActions(actions);
                }, args.a.explanation_delay);
            } else {
                twView.updateActions(actions);
            }
        });
    };

    twView.states['qn-startreview'] = function (curState) {
        twView.renderReviewForm();
        twView.updateActions([null, 'qn-submitreview']);
    };

    twView.states['qn-submitreview'] = function (curState) {
        return quiz.setQuestionReview(serializeForm(twView.jqQuiz.children('form')[1])).then(function (args) {
            var actions = twView.postQuestionActions;
            if (args.practiceAllowed > 0) {
                actions = twView.postQuestionActions.filter(function (a) { return a !== 'quiz-practice'; });
            }
            twMenu.syncAttempt(false);

            twView.updateActions(actions);
        });
    };

    twView.stateMachine(function updateState(curState, fallback) {
        twTimer.stop();
        fallback(curState);
    });
}(window, jQuery));

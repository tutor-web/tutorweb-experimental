"use strict";
/*jslint nomen: true, plusplus: true, unparam: true, todo: true*/
var test = require('tape');

var Quiz = require('../lib/quizlib.js');
var tk = require('timekeeper');
var Promise = require('es6-promise').Promise;

function broken_test(name, fn) {
    return fn;
}

function MockLocalStorage() {
    this.obj = {};
    this.length = 0;

    this.removeItem = function (key) {
        this.length--;
        return delete this.obj[key];
    };

    this.getItem = function (key) {
        var value = this.obj[key];
        return value === undefined ? null : value;
    };

    this.setItem = function (key, value) {
        if (!this.obj.hasOwnProperty(key)) {
            this.length++;
        }
        this.obj[key] = value;
        return value;
    };

    this.key = function (i) {
        return Object.keys(this.obj)[i];
    };
}

function MockAjaxApi() {
    this.count = 0;
    this.responses = {};
    this.data = {};

    this.getHtml = function (uri) {
        return this.block('GET ' + uri + ' ' + this.count++, undefined);
    };

    this.getJson = function (uri) {
        return this.block('GET ' + uri + ' ' + this.count++, undefined);
    };

    this.postJson = function (uri, data) {
        return this.block('POST ' + uri + ' ' + this.count++, data);
    };

    this.ajax = function (call) {
        return this.block(call.type + ' ' + call.url + ' ' + this.count++);
    };

    /** Block until responses[promiseId] contains something to resolve to */
    this.block = function (promiseId, data) {
        var self = this, timerTick = 10;
        //console.trace(promiseId);
        self.responses[promiseId] = null;
        this.data[promiseId] = data;

        return new Promise(function (resolve, reject) {
            setTimeout(function tick() {
                var r = self.responses[promiseId];
                if (!r) {
                    //console.log("WAITING: " + promiseId);
                    return setTimeout(tick(), timerTick);
                }

                delete self.responses[promiseId];
                delete self.data[promiseId];
                if (r instanceof Error) {
                    reject(r);
                } else {
                    resolve(r);
                }
            }, timerTick);
        });
    };

    this.getQueue = function () {
        return Object.keys(this.responses);
    };

    this.waitForQueue = function (expectedResponses) {
        var self = this,
            waited = 0;

        function allEqual(a, b) {
            var i;

            if (a.length !== b.length) {
                return false;
            }

            for (i = 0; i < a.length; i++) {
                if (a[i] !== b[i]) {
                    return false;
                }
            }
            return true;
        }

        return new Promise(function pollQueue(resolve, reject) {
            if (allEqual(Object.keys(self.responses), expectedResponses)) {
                resolve(self.responses);
            } else if (waited > 10) {
                reject(self.responses);
            } else {
                waited++;
                setTimeout(pollQueue.bind(null, resolve), 5);
            }
        });
    };

    this.setResponse = function (promiseId, ret) {
        this.responses[promiseId] = ret;
        return ret;
    };
}

function getQn(quiz, practiceMode) {
    return quiz.getNewQuestion({practice: practiceMode});
}
function setAns(quiz, choice) {
    return quiz.setQuestionAnswer(
        typeof choice === "object" ? choice
            : [{name: "answer", value: choice}]
    );
}
function setCurLec(quiz, tutUri, lecUri) {
    return quiz.setCurrentLecture({
        lecUri: lecUri,
    });
}
function newTutorial(quiz, tut_uri, extra_settings, question_counts) {
    var question_objects = {},
        settings = { "hist_sel": '0' };

    Object.keys(extra_settings || {}).map(function (k) {
        settings[k] = extra_settings[k];
    });

    return quiz.insertTutorial(tut_uri, 'UT tutorial', question_counts.map(function (question_count, lec_i) {
        // Make an array (question_count) elements long
        var x_long_arr = [];
        x_long_arr.length = question_count;
        x_long_arr = Array.apply(null, x_long_arr);

        return {
            "answerQueue": [],
            "questions": x_long_arr.map(function (ignore, qn_i) {
                var qn_uri = tut_uri + ":lec" + lec_i + ":qn" + qn_i;

                question_objects[qn_uri] = {
                    "text": '<div>The symbol for the set of all irrational numbers is... (a)</div>',
                    "choices": [
                        '<div>$\\mathbb{R} \\backslash \\mathbb{Q}$ (me)</div>',
                        '<div>$\\mathbb{Q} \\backslash \\mathbb{R}$</div>',
                        '<div>$\\mathbb{N} \\cap \\mathbb{Q}$</div>' ],
                    "shuffle": [0, 1, 2],
                    "answer": {
                        "explanation": "<div>\nThe symbol for the set of all irrational numbers (a)\n</div>",
                        "correct": [0]
                    }
                };

                return { "uri": qn_uri, "chosen": qn_i * 20, "correct": 100 };
            }),
            "settings": settings,
            "uri": tut_uri + ":lec" + lec_i,
            "question_uri": tut_uri + ":lec" + lec_i + ":all-questions",
        };
    }), question_objects);
}

// Find the first answer in qn that is correct
function chooseAnswer(args, correct) {
    var i;
    for (i = 0; i < args.qn.choices.length; i++) {
        if (args.qn.choices[i].indexOf('(me)') > -1) {
            if (correct) {
                return args.a.ordering.indexOf(i);
            }
        } else {
            if (!correct) {
                return args.a.ordering.indexOf(i);
            }
        }
    }
    throw "No suitable answer";
}


function test_utils() {
    var utils = {};

    utils.utTutorial = { "title": "UT tutorial", "lectures": []};

    utils.utTutorial.lectures.push({
        "answerQueue": [],
        "questions": [
            {"uri": "ut:question0", "chosen": 20, "correct": 100},
            {"uri": "ut:question1", "chosen": 40, "correct": 100},
            {"uri": "ut:question2", "chosen": 60, "correct": 100},
        ],
        "settings": {
            "hist_sel": 0,
        },
        "uri": "ut:lecture0",
        "question_uri": "ut:lecture0:all-questions",
    });

    utils.utQuestions = {
        "ut:question0" : {
            "text": '<div>The symbol for the set of all irrational numbers is... (a)</div>',
            "choices": [
                '<div>$\\mathbb{R} \\backslash \\mathbb{Q}$ (me)</div>',
                '<div>$\\mathbb{Q} \\backslash \\mathbb{R}$</div>',
                '<div>$\\mathbb{N} \\cap \\mathbb{Q}$</div>' ],
            "shuffle": [0, 1, 2],
            "answer": {
                "explanation": "<div>\nThe symbol for the set of all irrational numbers (a)\n</div>",
                "correct": [0]
            }
        },
        "ut:question1" : {
            "text": '<div>The symbol for the set of all irrational numbers is... (b)</div>',
            "choices": [
                '<div>$\\mathbb{R} \\backslash \\mathbb{Q}$ (me)</div>',
                '<div>$\\mathbb{Q} \\backslash \\mathbb{R}$</div>',
                '<div>$\\mathbb{N} \\cap \\mathbb{Q}$ (me)</div>' ],
            "shuffle": [0, 1],
            "answer": {
                "explanation": "<div>\nThe symbol for the set of all irrational numbers (b)\n</div>",
                "correct": [0, 2]
            }
        },
        "ut:question2" : {
            "text": '<div>The symbol for the set of all irrational numbers is... (c)</div>',
            "choices": [
                '<div>$\\mathbb{R} \\backslash \\mathbb{Q} (me)$</div>',
                '<div>$\\mathbb{Q} \\backslash \\mathbb{R}$</div>',
                '<div>$\\mathbb{N} \\cap \\mathbb{Q}$</div>' ],
            "shuffle": [0, 1, 2],
            "answer": {
                "explanation": "<div>\nThe symbol for the set of all irrational numbers (c)\n</div>",
                "correct": [0]
            }
        },
    };

    /** Configure a simple tutorial/lecture, ready for questions */
    utils.defaultLecture = function (quiz, settings) {
        return quiz.insertTutorial('ut:tutorial0', 'UT tutorial', [
            {
                "answerQueue": [],
                "questions": [
                    {"uri": "ut:question0", "chosen": 20, "correct": 100},
                    {"uri": "ut:question1", "chosen": 40, "correct": 100},
                    {"uri": "ut:question2", "chosen": 40, "correct": 100},
                ],
                "settings": settings || { "hist_sel": '0' },
                "uri": "ut:lecture0",
                "question_uri": "ut:lecture0:all-questions",
            },
        ], utils.utQuestions).then(function () {
            return quiz.setCurrentLecture({'lecUri': 'ut:lecture0'});
        });
    };

    return utils;
}

broken_test('_getAvailableLectures', function (t) {
    var ls = new MockLocalStorage(),
        quiz = new Quiz(ls),
        utils = test_utils();

    return utils.defaultLecture(quiz).then(function (args) {
        // At the start, everything should be synced
        return quiz.getAvailableLectures();
    }).then(function (subs) {
        t.deepEqual(subs.subscriptions, { children: [
            { id: 'ut:tutorial0', title: 'UT tutorial', children: [
                { uri: 'ut:lecture0', title: 'Lecture ut:lecture0' },
            ]},
        ]});
        t.deepEqual(subs.lectures, {
            'ut:lecture0': { grade: '', synced: true, offline: true },
        });
    }).then(function (args) {
        // Answer a question
        return (getQn(quiz, false));
    }).then(function (args) {
        return (setAns(quiz, 0));
    }).then(function (args) {
        // Now one is unsynced
        return quiz.getAvailableLectures();
    }).then(function (subs) {
        var gradeStr;

        if (JSON.parse(ls.getItem('ut:lecture0')).answerQueue[0].correct) {
            gradeStr = 'Answered 1 questions, 1 correctly.\nYour grade: 3.5';
        } else {
            gradeStr = 'Answered 1 questions, 0 correctly.\nYour grade: 0';
        }

        t.deepEqual(subs.subscriptions, { children: [
            { id: 'ut:tutorial0', title: 'UT tutorial', children: [
                { uri: 'ut:lecture0', title: 'Lecture ut:lecture0' },
            ]},
        ]});
        t.deepEqual(subs.lectures, {
            'ut:lecture0': { grade: gradeStr, synced: false, offline: true },
        });

    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

/** Should only remove genuinely unused objects */
broken_test('_removeUnusedObjects', function (t) {
    var ls = new MockLocalStorage(),
        aa = new MockAjaxApi(),
        quiz = new Quiz(ls, aa),
        ajaxPromise,
        utils = test_utils();

    // Load associated questions and a random extra
    ls.setItem('camel', 'yes');

    return quiz.insertTutorial(
        'ut:tutorial0',
        utils.utTutorial.title,
        utils.utTutorial.lectures,
        utils.utQuestions
    ).then(function () {

        t.deepEqual(Object.keys(ls.obj).sort(), [
            '_subscriptions',
            'camel',
            'ut:lecture0',
            'ut:question0',
            'ut:question1',
            'ut:question2',
        ]);

        ajaxPromise = quiz.syncLecture('ut:lecture0', true);
        return aa.waitForQueue(["POST ut:lecture0 0"]);

    }).then(function () {
        // Update lecture with new list of questions
        utils.utTutorial.lectures[0].questions = [
            {"uri": "ut:question0", "chosen": 20, "correct": 100},
            {"uri": "ut:question3", "chosen": 20, "correct": 100},
        ];
        aa.setResponse('POST ut:lecture0 0', utils.utTutorial.lectures[0]);
        return aa.waitForQueue(["GET ut:question3 1"]);

    }).then(function () {
        // Give it the question too, wait for finish.
        aa.setResponse('GET ut:question3 1', utils.utQuestions['ut:question1']);
        return ajaxPromise;
    }).then(function () {
        // syncLecture tidies up the questions
        t.deepEqual(Object.keys(ls.obj).sort(), [
            '_subscriptions',
            'ut:lecture0',
            'ut:question0',
            'ut:question3',
        ]);

        // RemoveUnused does too
        ls.setItem('orange', 'yes');
        return quiz.removeUnusedObjects();
    }).then(function () {
        t.deepEqual(Object.keys(ls.obj).sort(), [
            '_subscriptions',
            'ut:lecture0',
            'ut:question0',
            'ut:question3',
        ]);
    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

/** syncLecture should maintain any unsynced answerQueue entries */
broken_test('_syncLecture', function (t) {
    var ls = new MockLocalStorage(),
        aa = new MockAjaxApi(),
        quiz = new Quiz(ls, aa),
        assignedQns = [],
        ajaxPromise = null,
        opStatus = {},
        utils = test_utils();

    function logProgress(s, t, msg) {
        opStatus = { succeeded: s, total: t, message: msg };
    }

    return quiz.insertTutorial('ut:tutorial0', 'UT tutorial', [
        {
            "answerQueue": [],
            "questions": [
                {"uri": "ut:question0", "chosen": 20, "correct": 100},
                {"uri": "ut:question1", "chosen": 40, "correct": 100},
                {"uri": "ut:question2", "chosen": 40, "correct": 100},
            ],
            "settings": { "hist_sel": 0 },
            "uri": "ut:lecture0",
            "question_uri": "ut:lecture0:all-questions",
        },
    // No answers yet.
    ], utils.utQuestions).then(function () {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture0'});

    // Should be nothing to do at start
    }).then(function (args) {
        ajaxPromise = quiz.syncLecture(null, false);
        return ajaxPromise;

    }).then(function (args) {
        t.deepEqual(aa.getQueue(), []);
        t.deepEqual(args, undefined);

    // Can force something to happen though
    }).then(function (args) {
        ajaxPromise = quiz.syncLecture(null, true, logProgress);
        return aa.waitForQueue(["POST ut:lecture0 0"]);

    }).then(function () {
        t.deepEqual(opStatus, { succeeded: 0, total: 3, message: 'Fetching lecture...' });
        t.deepEqual(aa.data['POST ut:lecture0 0'].answerQueue, []);
        aa.setResponse('POST ut:lecture0 0', aa.data['POST ut:lecture0 0']);
        return ajaxPromise;

    // Answer some questions
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        t.ok(args.answerData.explanation.indexOf('The symbol for the set') !== -1); // Make sure answerData gets through
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return args;

    // Now should want to sync
    }).then(function (args) {
        ajaxPromise = quiz.syncLecture(null, false, logProgress);
        return aa.waitForQueue(["POST ut:lecture0 1"]);

    }).then(function () {
        t.deepEqual(aa.data['POST ut:lecture0 1'].answerQueue.map(function (a) { return a.synced; }), [
            false, false, false
        ]);
        t.deepEqual(opStatus, { succeeded: 0, total: 3, message: 'Fetching lecture...' });
        return null; //NB: Leave it waiting

    // Answer another question before we do.
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));

    // Finish the AJAX call
    }).then(function (args) {
        aa.setResponse('POST ut:lecture0 1', {
            "answerQueue": [ {"camel" : 3, "time_end": 5, "lec_answered": 8, "lec_correct": 3, "synced" : true} ],
            "questions": [
                {"uri": "ut:question0", "chosen": 20, "correct": 100},
                {"uri": "ut:question2", "chosen": 40, "correct": 100},
                {"uri": "ut:question8", "chosen": 40, "correct": 100},
            ],
            "removed_questions": ['ut:question1'],
            "settings": { "any_setting": 0.5 },
            "uri": "ut:lecture0",
            "question_uri": "ut:lecture0:all-questions",
        });
        return aa.waitForQueue(["GET ut:question8 2"]);

    // The missing question was fetched
    }).then(function () {
        t.deepEqual(opStatus, { succeeded: 1, total: 4, message: 'Fetching questions...' });
        aa.setResponse('GET ut:question8 2', {
            "text": '<div>The symbol for the set of all irrational numbers is... (a)</div>',
            "choices": [
                '<div>$\\mathbb{R} \\backslash \\mathbb{Q}$ (me)</div>',
                '<div>$\\mathbb{Q} \\backslash \\mathbb{R}$</div>',
                '<div>$\\mathbb{N} \\cap \\mathbb{Q}$</div>'
            ],
            "shuffle": [0, 1, 2],
            "answer": {
                "explanation": "<div>\nThe symbol for the set of all irrational numbers (a)\n</div>",
                "correct": [0]
            },
        });
        return ajaxPromise;
    }).then(function (args) {
        t.equal(
            JSON.parse(ls.getItem('ut:question8')).text,
            '<div>The symbol for the set of all irrational numbers is... (a)</div>'
        );

    // Lecture should have been updated, with additional question kept
    }).then(function (args) {
        var lec = JSON.parse(ls.getItem('ut:lecture0'));
        t.equal(lec.answerQueue.length, 2);
        t.deepEqual(lec.answerQueue[0], {
            "time_end": 5,
            "camel" : 3,
            "lec_answered": 8,
            "lec_correct": 3,
            "practice_answered": 0,
            "practice_correct": 0,
            "synced" : true,
        });
        t.equal(lec.answerQueue[1].uri, assignedQns[3].uri);
        // Counts have been bumped up accordingly
        t.equal(lec.answerQueue[1].lec_answered, 9);
        t.equal(lec.answerQueue[1].lec_correct, lec.answerQueue[1].correct ? 4 : 3);
        // Practice counts initialised
        t.equal(lec.answerQueue[1].practice_answered, 0);
        t.equal(lec.answerQueue[1].practice_correct, 0);
        t.deepEqual(lec.answerQueue[1].synced, false);
        t.deepEqual(lec.settings, { "any_setting": 0.5 });

    // Take some questions, leave one unaswered, sync
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);

        ajaxPromise = quiz.syncLecture(null, false);
        return aa.waitForQueue(["POST ut:lecture0 3"]);

    }).then(function () {
        aa.setResponse('POST ut:lecture0 3', {
            "answerQueue": [ {"camel" : 3, "synced" : true} ],
            "questions": [
                {"uri": "ut:question0", "chosen": 20, "correct": 100},
                {"uri": "ut:question2", "chosen": 40, "correct": 100},
                {"uri": "ut:question8", "chosen": 40, "correct": 100},
            ],
            "removed_questions": ['ut:question1'],
            "settings": { "hist_sel": 0 },
            "uri": "ut:lecture0",
            "question_uri": "ut:lecture0:all-questions",
        });
        return ajaxPromise;

    // Unanswered question still on end
    }).then(function (args) {
        var lec = JSON.parse(ls.getItem('ut:lecture0'));
        t.equal(lec.answerQueue.length, 2);
        t.deepEqual(lec.answerQueue[0], {"camel" : 3, "synced" : true, lec_answered: 0, lec_correct: 0, practice_answered: 0, practice_correct: 0});
        t.equal(assignedQns.length, 6);
        t.equal(lec.answerQueue[1].uri, assignedQns[assignedQns.length - 1].uri);

    // Answer question, ask a practice question. Answer practice question mid-sync
    }).then(function (args) {
        return (setAns(quiz, 0));
    }).then(function (args) {
        return (getQn(quiz, true));
    }).then(function (args) {
        assignedQns.push(args.a);
        ajaxPromise = quiz.syncLecture(null, false);
        return aa.waitForQueue(['POST ut:lecture0 4']);

    }).then(function () {
        return setAns(quiz, 0);
    }).then(function (args) {
        aa.setResponse('POST ut:lecture0 4', {
            "answerQueue": [ {"camel" : 3, "lec_answered": 8, "lec_correct": 3, "synced" : true} ],
            "questions": [
                {"uri": "ut:question0", "chosen": 20, "correct": 100},
                {"uri": "ut:question2", "chosen": 40, "correct": 100},
                {"uri": "ut:question8", "chosen": 40, "correct": 100},
            ],
            "removed_questions": ['ut:question1'],
            "settings": { "hist_sel": 0 },
            "uri": "ut:lecture0",
            "question_uri": "ut:lecture0:all-questions",
        });
        return ajaxPromise;
    }).then(function (args) {
        var lec = JSON.parse(ls.getItem('ut:lecture0'));
        t.equal(lec.answerQueue.length, 2);
        t.equal(assignedQns.length, 7);
        t.equal(lec.answerQueue[1].lec_answered, 9);
        t.equal(lec.answerQueue[1].lec_correct, assignedQns[6].correct ? 4 : 3);
        t.equal(lec.answerQueue[1].practice_answered, 1);
        t.equal(lec.answerQueue[1].practice_correct, assignedQns[6].correct ? 1 : 0);

    // Counts start from zero if server doesn't tell us otherwise
    }).then(function (args) {
        var syncPromise = quiz.syncLecture(null, false);

        return aa.waitForQueue(['POST ut:lecture0 5']).then(function (args) {
            aa.setResponse('POST ut:lecture0 5', {
                "answerQueue": [
                    {"correct": true,  "practice": false, "synced" : true, "time_end": 1 },
                    {"correct": true,  "practice": false, "synced" : true, "time_end": 2 },
                    {"correct": false, "practice": true,  "synced" : true, "time_end": 3 },
                    {"correct": true,  "practice": true,  "synced" : true, "time_end": 4 },
                    {"correct": true,  "practice": false, "synced" : true, "time_end": 5 },
                ],
                "questions": [
                    {"uri": "ut:question0", "chosen": 20, "correct": 100},
                    {"uri": "ut:question2", "chosen": 40, "correct": 100},
                    {"uri": "ut:question8", "chosen": 40, "correct": 100},
                ],
                "settings": { "hist_sel": 0 },
                "uri": "ut:lecture0",
                "question_uri": "ut:lecture0:all-questions",
            });
            return syncPromise;
        });
    }).then(function (args) {
        var lec = JSON.parse(ls.getItem('ut:lecture0'));
        function aqProperty(k) {
            return lec.answerQueue.map(function (a) { return a[k]; });
        }

        t.deepEqual(aqProperty('lec_answered'), [1, 2, 3, 4, 5]);
        t.deepEqual(aqProperty('lec_correct'),  [1, 2, 2, 3, 4]);
        t.deepEqual(aqProperty('practice_answered'), [0, 0, 1, 2, 2]);
        t.deepEqual(aqProperty('practice_correct'),  [0, 0, 0, 1, 1]);

    // Do a sync with the wrong user, we complain.
    }).then(function (args) {
        var lec = JSON.parse(ls.getItem('ut:lecture0'));

        lec.user = 'ut_student';
        ls.setItem('ut:lecture0', JSON.stringify(lec));
        ajaxPromise = quiz.syncLecture(null, true);
        return aa.waitForQueue(['POST ut:lecture0 6']);

    }).then(function (args) {
        aa.setResponse('POST ut:lecture0 6', {
            "answerQueue": [],
            "user": "not_the_user_you_are_looking_for",
            "questions": [],
            "settings": { "hist_sel": 0 },
            "uri": "ut:lecture0",
            "question_uri": "ut:lecture0:all-questions",
        });
        return ajaxPromise.then(function () { t.fail(); }).catch(function (err) {
            var lec = JSON.parse(ls.getItem('ut:lecture0'));

            t.ok(err.message.indexOf("not_the_user_you_are_looking_for") > -1);
            t.equal(lec.answerQueue.length, 5);
            t.equal(lec.questions.length, 3);
            t.ok(lec.user !== "not_the_user_you_are_looking_for");
        });

    // If lots of questions are added, just fetch the whole lot
    }).then(function (args) {
        ajaxPromise = quiz.syncLecture(null, true);
        return aa.waitForQueue(['POST ut:lecture0 7']);
    }).then(function (args) {
        aa.setResponse('POST ut:lecture0 7', {
            "answerQueue": [],
            "user": 'ut_student',
            "questions": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15].map(function (i) {
                return {"uri": "ut:question" + i, "chosen": 20, "correct": 100};
            }),
            "settings": { "hist_sel": 0 },
            "uri": "ut:lecture0",
            "question_uri": "ut:lecture0:all-questions",
        });
        return aa.waitForQueue(['GET ut:lecture0:all-questions 8']);
    }).then(function (args) {
        var newQuestions = {};

        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15].map(function (i) {
            newQuestions['ut:question' + i] = {
                text: "This is Question " + i,
            };
        });
        aa.setResponse('GET ut:lecture0:all-questions 8', newQuestions);
        return ajaxPromise.then(function () {
            // All new questions updated
            Object.keys(newQuestions).map(function (k) {
                t.deepEqual(JSON.parse(ls.getItem(k)), newQuestions[k]);
            });
        });

    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});
//TODO: Test that Other parameters can be modified, e.g. title.

broken_test('_setQuestionAnswer', function (t) {
    var ls = new MockLocalStorage(),
        quiz = new Quiz(ls),
        assignedQns = [],
        startTime = Math.round((new Date()).getTime() / 1000) - 1,
        utils = test_utils();

    return utils.defaultLecture(quiz).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, []));

    // Fail to answer question, should get a null for the student answer
    }).then(function (args) {
        var lec = JSON.parse(ls.getItem('ut:lecture0'));
        t.equal(lec.answerQueue.length, 1);
        t.ok(lec.answerQueue[0].time_end > startTime);
        t.equal(typeof lec.answerQueue[0].student_answer, "object");
        t.equal(lec.answerQueue[0].student_answer, null);
        t.equal(typeof lec.answerQueue[0].selected_answer, "object");
        t.equal(lec.answerQueue[0].selected_answer, null);

    // Add a tutorial with a template question
    }).then(function (args) {
        return quiz.insertTutorial('ut:tmpltutorial', 'UT template qn tutorial', [
            {
                "answerQueue": [],
                "questions": [
                    {"uri": "ut:tmplqn0", "online_only": false},  // NB: Would normally be true
                ],
                "settings": { "hist_sel": 0 },
                "uri": "ut:lecture0",
                "question_uri": "ut:lecture0:all-questions",
            },
        ], {
            "ut:tmplqn0": {
                "_type": "template",
                "title": "Write a question about fish",
                "hints": "<div class=\"ttm-output\">You could ask something about their external appearance</div>",
                "example_text": "How many toes?",
                "example_explanation": "why would they have toes?'",
                "example_choices": ["4", "5"],
                "student_answer": {},
            },
        });
    }).then(function (args) {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture0'});

    // When dealing with template questions, should decode form data
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        t.equal(args.a.question_type, "template");
        return (setAns(quiz, [
            { name: "text", value: "How many toes?"},
            { name: "choice_0", value: "1"},
            { name: "choice_1", value: "4"},
            { name: "choice_2", value: "A zillion"},
            { name: "choice_2_correct", value: "on"},
            { name: "explanation", value: "Lots of toes!"},
        ]));
    }).then(function (args) {
        t.deepEqual(args.answerData, {}); // No answerdata for template questions
        t.equal(args.a.correct, true);
        t.deepEqual(args.a.student_answer, {
            choices: [
                { answer: '1', correct: false },
                { answer: '4', correct: false },
                { answer: 'A zillion', correct: true }
            ],
            text: 'How many toes?',
            explanation: 'Lots of toes!'
        });

    // When dealing with template questions, should decode form data
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        t.equal(args.a.question_type, "template");
        return (setAns(quiz, [
            { name: "text", value: "How many $toes$?"},
            { name: "choice_2", value: "A zillion"},
            { name: "choice_0", value: "1"},
            { name: "choice_0_correct", value: "yay"},
            { name: "choice_1", value: "4"},
            { name: "choice_1_correct", value: "true"},
            { name: "explanation", value: "Lots of toes!"},
        ]));
    }).then(function (args) {
        t.equal(args.a.correct, true);
        t.deepEqual(args.a.student_answer, {
            choices: [
                { answer: '1', correct: true },
                { answer: '4', correct: true },
                { answer: 'A zillion', correct: false }
            ],
            text: 'How many $toes$?',
            explanation: 'Lots of toes!'
        });

    // No answer should still result in null
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        t.equal(args.a.question_type, "template");
        return (setAns(quiz, []));
    }).then(function (args) {
        t.deepEqual(args.answerData, {});
        t.equal(args.a.correct, false);
        t.deepEqual(args.a.student_answer, null);

    // Reworking a question should result in null too
    }).then(function (args) {
        quiz.insertQuestions({
            "ut:tmplqn0": {
                "_type": "template",
                "title": "Write a question about fish",
                "hints": "<div class=\"ttm-output\">You could ask something about their external appearance</div>",
                "example_text": "How about a simple sum?",
                "example_explanation": "why would they have toes?'",
                "example_choices": ["4", "5"],
                "student_answer": {text: "<div>What's 1+1?</div>", choices: []},
            }
        });
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        t.equal(args.a.question_type, "template");
        return (setAns(quiz, []));
    }).then(function (args) {
        t.equal(args.a.correct, null);
        t.deepEqual(args.a.student_answer, null);
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        t.equal(args.a.question_type, "template");
        return (setAns(quiz, [
            { name: "text", value: "How many toes?"},
            { name: "choice_0", value: "1"},
            { name: "choice_1", value: "4"},
            { name: "choice_2", value: "A zillion"},
            { name: "choice_2_correct", value: "on"},
            { name: "explanation", value: "Lots of toes!"},
        ]));
    }).then(function (args) {
        t.equal(args.a.correct, null);
        t.deepEqual(args.a.student_answer.text, "How many toes?");

    // Add a tutorial with a usergenerated question
    }).then(function (args) {
        return quiz.insertTutorial('ut:ugtutorial', 'UT template qn tutorial', [
            {
                "answerQueue": [],
                "questions": [
                    {"uri": "ut:ugqn0", "online_only": false},  // NB: Would normally be true
                ],
                "settings": { "hist_sel": 0 },
                "uri": "ut:lecture0",
                "question_uri": "ut:lecture0:all-questions",
            },
        ], {
            "ut:ugqn0": {
                "_type": "usergenerated",
                "question_id": 999,
                "text": "Riddle me this.",
                "choices": ["Yes", "No"],
                "shuffle": [0, 1],
                "answer": {
                    "correct": [0],
                    "explanation": "It'd be boring otherwise"
                }
            },
        });
    }).then(function (args) {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture0'}, function () { return null; });

    // Fetch a usergenerated question and answer it, should be marked but not "answered"
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        return (setAns(quiz, [
            { name: "answer", value: args.a.ordering.indexOf(0).toString() }
        ]));
    }).then(function (args) {
        t.equal(args.answerData.explanation, "It'd be boring otherwise");
        t.ok(!args.a.hasOwnProperty("correct"));
        t.ok(!args.a.hasOwnProperty("time_end"));
        t.deepEqual(args.a.student_answer, { choice: 0 });

        // Could have only ordered the questions 2 ways
        if (args.a.ordering[0] === 0) {
            t.deepEqual(args.a.ordering, [0, 1]);
            t.deepEqual(args.a.ordering_correct, [true, false]);
        } else {
            t.deepEqual(args.a.ordering, [1, 0]);
            t.deepEqual(args.a.ordering_correct, [false, true]);
        }
        return args;

    // Try again with a comment, even empty should be properly answered
    }).then(function (args) {
        return (setAns(quiz, [
            { name: "answer", value: args.a.ordering.indexOf(0).toString() },
            { name: "comments", value: "" },
        ]));
    }).then(function (args) {
        t.ok(!args.a.hasOwnProperty("correct")); // NB: Never have correct
        t.ok(args.a.hasOwnProperty("time_end"));
        t.deepEqual(args.a.student_answer, { choice: 0, comments: "" });

    // Start again, fill in everything
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        return (setAns(quiz, [
            { name: "answer", value: args.a.ordering.indexOf(1).toString() },
            { name: "comments", value: "Boo!" },
            { name: "rating", value: "50" },
        ]));
    }).then(function (args) {
        t.ok(!args.a.hasOwnProperty("correct")); // NB: Never have correct
        t.ok(args.a.hasOwnProperty("time_end"));
        t.deepEqual(args.a.student_answer, { choice: 1, comments: "Boo!", rating: 50 });

    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

broken_test('_setQuestionAnswer_exam', function (t) {
    var ls = new MockLocalStorage(),
        quiz = new Quiz(ls);

    newTutorial(quiz, "ut:tut0", { grade_algorithm: "ratiocorrect" }, [5, 10]).then(function () {
        return setCurLec(quiz, "ut:tut0", "ut:tut0:lec0");

    // Get a question and answer it incorrectly, score is 0 / 5 * 10
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        return (setAns(quiz, chooseAnswer(args, false)));
    }).then(function (args) {
        t.deepEqual(args.a.grade_after, 0);

    // Get a question and answer it correctly, score is 1 / 5 * 10
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        return (setAns(quiz, chooseAnswer(args, true)));
    }).then(function (args) {
        t.deepEqual(args.a.grade_after, 2);

    // Get a question and answer it correctly, score is 2 / 5 * 10
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        return (setAns(quiz, chooseAnswer(args, true)));
    }).then(function (args) {
        t.deepEqual(args.a.grade_after, 4);

    // Get a question and answer it incorrectly, score is 2 / 5 * 10
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        return (setAns(quiz, chooseAnswer(args, false)));
    }).then(function (args) {
        t.deepEqual(args.a.grade_after, 4);

    // Switch lectures to one with 10 questions
    }).then(function (args) {
        return (setCurLec(quiz, "ut:tut0", "ut:tut0:lec1"));

    // Get a question and answer it correctly, score is 1 / 10 * 10
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        return (setAns(quiz, chooseAnswer(args, true)));
    }).then(function (args) {
        t.deepEqual(args.a.grade_after, 1);

    // Get a question and answer it correctly, score is 2 / 10 * 10
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        return (setAns(quiz, chooseAnswer(args, true)));
    }).then(function (args) {
        t.deepEqual(args.a.grade_after, 2);

    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

/** Explanation delay should increase with incorrect questions */
broken_test('_explanationDelay', function (t) {
    var ls = new MockLocalStorage(),
        quiz = new Quiz(ls),
        utils = test_utils();

    utils.defaultLecture(quiz, {
        studytime_answeredfactor: '10',
        studytime_factor: '2',
        studytime_max: '1000',
    }).then(function (args) {
        return (getQn(quiz, false));

    // Get question wrong, already have a delay set
    }).then(function (args) {
        return (setAns(quiz, chooseAnswer(args, false)));
    }).then(function (args) {
        t.deepEqual(args.a.correct, false);
        t.deepEqual(args.a.explanation_delay, 2);
        return (getQn(quiz, false));

    // This increases with next question
    }).then(function (args) {
        return (setAns(quiz, chooseAnswer(args, false)));
    }).then(function (args) {
        t.deepEqual(args.a.correct, false);
        t.deepEqual(args.a.explanation_delay, 2 * 2 + 10);
        return (getQn(quiz, false));

    // Correct answer resets
    }).then(function (args) {
        return (setAns(quiz, chooseAnswer(args, true)));
    }).then(function (args) {
        t.deepEqual(args.a.correct, true);
        t.deepEqual(args.a.explanation_delay, 2 * 10);
        return (getQn(quiz, false));

    // Get it wrong, but took some time, delay isn't noticable
    }).then(function (args) {
        tk.travel(new Date((new Date()).getTime() + 50000));
        return (setAns(quiz, chooseAnswer(args, false)));
    }).then(function (args) {
        t.deepEqual(args.a.correct, false);
        t.deepEqual(args.a.explanation_delay, 0); // NB: Would be 1 * 2 + 3 * 10 - 50
        tk.reset();
        return (getQn(quiz, false));

    // Next time it is
    }).then(function (args) {
        tk.travel(new Date((new Date()).getTime() + 30000));
        return (setAns(quiz, chooseAnswer(args, false)));
    }).then(function (args) {
        t.deepEqual(args.a.correct, false);
        t.deepEqual(args.a.explanation_delay, 14); // NB: Would be 2 * 2 + 4 * 10 - 30
        tk.reset();
        return (getQn(quiz, false));

    }).then(function (args) {
        tk.reset();
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        tk.reset();
        t.end();
    });
});

/** We should get various strings encouraging users */
broken_test('_gradeSummaryStrings', function (t) {
    var ls = new MockLocalStorage(),
        quiz = new Quiz(ls),
        assignedQns = [],
        utils = test_utils();

    // Insert tutorial, no answers yet.
    return quiz.insertTutorial('ut:tutorial0', 'UT tutorial', [
        {
            "answerQueue": [],
            "questions": [
                {"uri": "ut:question0", "chosen": 20, "correct": 100},
                {"uri": "ut:question1", "chosen": 40, "correct": 100},
                {"uri": "ut:question2", "chosen": 40, "correct": 100},
            ],
            "settings": {
                "hist_sel": 0,
                "award_lecture_aced":  1024,
                "award_tutorial_aced": 10960, // NB: these values are mSMLY, need rounding
            },
            "uri": "ut:lecture0",
            "question_uri": "ut:lecture0:all-questions",
        },
    ], utils.utQuestions).then(function (args) {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture0'});

    // At start, we have no grade, but know how many SMLY we get,
    }).then(function (args) {
        return quiz.lectureGradeSummary();
    }).then(function (grade_summary) {
        t.equal(grade_summary.practice, undefined);
        t.equal(grade_summary.practiceStats, undefined);
        t.equal(grade_summary.stats, undefined);
        t.equal(grade_summary.grade, undefined);
        t.equal(grade_summary.encouragement, 'Win 1 SMLY if you ace this lecture, bonus 11 SMLY for acing whole tutorial');
        return (getQn(quiz, false));

    // Answer some questions, should see our grade
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return quiz.lectureGradeSummary().then(function (grade_summary) {
            t.equal(grade_summary.practice, undefined);
            t.equal(grade_summary.practiceStats, undefined);
            t.equal(grade_summary.stats, 'Answered 0 questions, 0 correctly.');
            t.equal(grade_summary.grade, 'Your grade: 0');
            t.equal(grade_summary.encouragement, 'Win 1 SMLY if you ace this lecture, bonus 11 SMLY for acing whole tutorial');
            return (setAns(quiz, chooseAnswer(args, true)));
        });
    }).then(function (args) {
        return quiz.lectureGradeSummary();
    }).then(function (grade_summary) {
        t.equal(grade_summary.practice, undefined);
        t.equal(grade_summary.practiceStats, undefined);
        t.equal(grade_summary.stats, 'Answered 1 questions, 1 correctly.');
        t.equal(grade_summary.grade, 'Your grade: 3.5');
        t.equal(grade_summary.encouragement, 'If you get the next question right: 6');

    }).then(function (args) {
        return (getQn(quiz, true));
    }).then(function (args) {
        return quiz.lectureGradeSummary().then(function (grade_summary) {
            t.equal(grade_summary.practice, "Practice mode");
            t.equal(grade_summary.practiceStats, "Answered 0 practice questions, 0 correctly.");
            t.equal(grade_summary.stats, 'Answered 1 questions, 1 correctly.');
            t.equal(grade_summary.grade, 'Your grade: 3.5');
            t.equal(grade_summary.encouragement, 'Win 1 SMLY if you ace this lecture, bonus 11 SMLY for acing whole tutorial');
            return (setAns(quiz, chooseAnswer(args, false)));
        });
    }).then(function (args) {
        return quiz.lectureGradeSummary();
    }).then(function (grade_summary) {
        t.equal(grade_summary.practice, "Practice mode");
        t.equal(grade_summary.practiceStats, "Answered 1 practice questions, 0 correctly.");

    // Stop it and tidy up
    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

/** lastEight should return last relevant questions */
test('_gradeSummarylastEight', function (t) {
    var ls = new MockLocalStorage(),
        quiz = new Quiz(ls),
        assignedQns = [],
        utils = test_utils();

    // Insert tutorial, no answers yet.
    return quiz.insertTutorial('ut:tutorial0', 'UT tutorial', [
        {
            "answerQueue": [],
            "questions": [
                {"uri": "ut:question0", "chosen": 20, "correct": 100},
                {"uri": "ut:question1", "chosen": 40, "correct": 100},
                {"uri": "ut:question2", "chosen": 40, "correct": 100},
            ],
            "settings": { "hist_sel": 0 },
            "uri": "ut:lecture0",
            "question_uri": "ut:lecture0:all-questions",
        },
    ], utils.utQuestions).then(function (args) {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture0'});

    // lastEight returns nothing
    }).then(function (args) {
        return quiz.lectureGradeSummary();
    }).then(function (grade_summary) {
        t.deepEqual(grade_summary.lastEight, []);

    // Answer some questions
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return quiz.lectureGradeSummary();
    }).then(function (grade_summary) {
        t.equal(grade_summary.lastEight.length, 3);
        t.equal(grade_summary.lastEight[0].uri, assignedQns[2].uri);
        t.equal(grade_summary.lastEight[1].uri, assignedQns[1].uri);
        t.equal(grade_summary.lastEight[2].uri, assignedQns[0].uri);

    // Unanswered questions don't count
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return quiz.lectureGradeSummary();
    }).then(function (grade_summary) {
        t.equal(grade_summary.lastEight.length, 3);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return quiz.lectureGradeSummary();
    }).then(function (grade_summary) {
        t.equal(grade_summary.lastEight.length, 4);
        t.equal(grade_summary.lastEight[3].uri, assignedQns[0].uri);

    // Practice questions don't count
    }).then(function (args) {
        return (getQn(quiz, true));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return (getQn(quiz, true));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return quiz.lectureGradeSummary();
    }).then(function (grade_summary) {
        t.equal(grade_summary.lastEight.length, 5);
        t.equal(grade_summary.lastEight[0].uri, assignedQns[6].uri);
        t.equal(grade_summary.lastEight[1].uri, assignedQns[3].uri);
        t.equal(grade_summary.lastEight[2].uri, assignedQns[2].uri);
        t.equal(grade_summary.lastEight[3].uri, assignedQns[1].uri);
        t.equal(grade_summary.lastEight[4].uri, assignedQns[0].uri);

    // Old questions don't count
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return (getQn(quiz, false));
    }).then(function (args) {
        assignedQns.push(args.a);
        return (setAns(quiz, 0));
    }).then(function (args) {
        return quiz.lectureGradeSummary();
    }).then(function (grade_summary) {
        t.equal(grade_summary.lastEight.length, 8);
        t.equal(grade_summary.lastEight[0].uri, assignedQns[11].uri);
        t.equal(grade_summary.lastEight[1].uri, assignedQns[10].uri);
        t.equal(grade_summary.lastEight[2].uri, assignedQns[9].uri);
        t.equal(grade_summary.lastEight[3].uri, assignedQns[8].uri);
        t.equal(grade_summary.lastEight[4].uri, assignedQns[7].uri);
        t.equal(grade_summary.lastEight[5].uri, assignedQns[6].uri);
        t.equal(grade_summary.lastEight[6].uri, assignedQns[3].uri);
        t.equal(grade_summary.lastEight[7].uri, assignedQns[2].uri);
    }).then(function (args) {
        t.end();
    });
});

/** Should update question count upon answering questions */
broken_test('_questionUpdate ', function (t) {
    var ls = new MockLocalStorage(),
        quiz = new Quiz(ls),
        assignedQns = [],
        qnBefore,
        utils = test_utils();

    // Emulate old onSuccess interface
    function gnq(opts, onSuccess) {
        quiz.getNewQuestion(opts).then(function (args) {
            onSuccess(args.qn, args.a);
        });
    }
    function sqa(opts, onSuccess) {
        quiz.setQuestionAnswer(opts).then(function (args) {
            onSuccess(args.a, args.answerData);
        });
    }

    // Turn questions into a hash for easy finding
    function qnHash() {
        var out = {};
        JSON.parse(ls.getItem('ut:lecture0')).questions.map(function (qn) {
            out[qn.uri] = {"chosen": qn.chosen, "correct": qn.correct};
        });
        return out;
    }

    // Insert tutorial, no answers yet.
    return quiz.insertTutorial('ut:tutorial0', 'UT tutorial', [
        {
            "answerQueue": [],
            "questions": [
                {"uri": "ut:question0", "chosen": 20, "correct": 100},
                {"uri": "ut:question1", "chosen": 40, "correct": 100},
                {"uri": "ut:question2", "chosen": 40, "correct": 100},
            ],
            "settings": { "hist_sel": 0 },
            "uri": "ut:lecture0",
            "question_uri": "ut:lecture0:all-questions",
        },
    ], utils.utQuestions).then(function (args) {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture0'});
    }).then(function (args) {
        qnBefore = qnHash();

        // Assign a question, should see jump in counts
        gnq({practice: true}, function (qn, a) {
            assignedQns.push(a);
            sqa([{name: "answer", value: 0}], function () {
                t.equal(
                    qnBefore[assignedQns[0].uri].chosen + 1,
                    qnHash()[assignedQns[0].uri].chosen
                );
                t.ok(
                    (qnBefore[assignedQns[0].uri].correct === qnHash()[assignedQns[0].uri].correct) ||
                        (qnBefore[assignedQns[0].uri].correct + 1 === qnHash()[assignedQns[0].uri].correct)
                );
            });
        });

    }).then(function (args) {
        tk.reset();
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

test('_setCurrentLecture_practiceAllowed', function (t) {
    var ls = new MockLocalStorage(),
        aa = new MockAjaxApi(),
        quiz = new Quiz(ls, aa),
        utils = test_utils();

    return quiz.insertTutorial('ut:tutorial0', 'UT tutorial', [
        {
            "uri": "ut:lecture0",
            "question_uri": "ut:lecture0:all-questions",
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            // Unlimited practicing
            "settings": { 'practice_after': 0, 'practice_batch': Infinity },
        }, {
            "uri": "ut:lecture1",
            "question_uri": "ut:lecture1:all-questions",
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            // Unlimited practicing, once we get to 10 questions
            "settings": { 'practice_after': 5, 'practice_batch': Infinity },
        }, {
            "uri": "ut:lecture2",
            "question_uri": "ut:lecture2:all-questions",
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            // 1 practice question per 2 real questions
            "settings": { 'practice_after': 2, 'practice_batch': 3 },
        },
    ], utils.utQuestions).then(function () {

        // Lecture0 always allows practice questions
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture0'});
    }).then(function (args) {
        t.equal(args.practiceAllowed, Infinity);
    }).then(function (args) {
        // Answer a practice question
        return getQn(quiz, true).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        // setQuestionAnswer says infinity too
        t.equal(args.practiceAllowed, Infinity);

        // Lecture1 allows practice questions once we get to 5
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture1'});
    }).then(function (args) {
        t.equal(args.practiceAllowed, 0);
        // getQn refuses to get practice questions
        return getQn(quiz, true).then(function () { t.fail(); }).catch(function (err) {
            t.ok(err.message.indexOf("No practice questions left") > -1);
        });
    }).then(function (args) {
        // Still not allowed after 4 real questions
        return getQn(quiz, false).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        return getQn(quiz, false).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        return getQn(quiz, false).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        return getQn(quiz, false).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        t.equal(args.practiceAllowed, 0);
    }).then(function (args) {
        // The fifth goes to infinity
        return getQn(quiz, false).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        t.equal(args.practiceAllowed, Infinity);
        // Doesn't change with practice
        return getQn(quiz, true).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        t.equal(args.practiceAllowed, Infinity);

        // Lecture2 allows practice questions once we get to 2
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture2'});
    }).then(function (args) {
        t.equal(args.practiceAllowed, 0);
        return getQn(quiz, false).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        t.equal(args.practiceAllowed, 0);
        return getQn(quiz, false).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        t.equal(args.practiceAllowed, 3);
        return getQn(quiz, false).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        t.equal(args.practiceAllowed, 3);
        return getQn(quiz, false).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        t.equal(args.practiceAllowed, 6);  // NB: We roll-over
        // Use them up with practice questions
        return getQn(quiz, true).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        t.equal(args.practiceAllowed, 5);
        return getQn(quiz, true).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        t.equal(args.practiceAllowed, 4);
        return getQn(quiz, true).then(setAns.bind(null, quiz, 0));
    }).then(function (args) {
        t.equal(args.practiceAllowed, 3);

    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

broken_test('_getNewQuestion', function (t) {
    var ls = new MockLocalStorage(),
        aa = new MockAjaxApi(),
        promise,
        quiz = new Quiz(ls, aa),
        assignedQns = [],
        startTime = Math.round((new Date()).getTime() / 1000) - 1,
        utils = test_utils();

    return quiz.insertTutorial('ut:tutorial0', 'UT tutorial', [
        {
            "answerQueue": [],
            "questions": [
                {"uri": "ut:question0", "chosen": 20, "correct": 100},
                {"uri": "ut:question1", "chosen": 40, "correct": 100},
                {"uri": "ut:question2", "chosen": 40, "correct": 100},
            ],
            "settings": { "hist_sel": '0' },
            "uri": "ut:lecture0",
            "question_uri": "ut:lecture0:all-questions",
        },
        {
            "answerQueue": [],
            "questions": [
                {"uri": "ut:question-a", "chosen": 20, "correct": 100, "online-only": "true"},
            ],
            "settings": { "hist_sel": '0' },
            "uri": "ut:lecture-online",
            "question_uri": "ut:lecture0:all-questions",
        },
    ], utils.utQuestions).then(function () {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture0'});
    }).then(function () {
        return quiz.getNewQuestion({practice: false});
    }).then(function (args) {
        var qn = args.qn, a = args.a,
            fixedOrdering = Array.apply(null, {length: qn.choices.length}).map(Number.call, Number);

        assignedQns.push(a);
        // Question data has been set up
        t.equal(a.synced, false);
        if (qn.shuffle.length < qn.choices.length) {
            // Not shuffling everything, so last item should always be last question.
            qn.shuffle[qn.shuffle.length - 1] = 2;
        }
        t.deepEqual(
            a.ordering.slice(0).sort(0),  // NB: Slice first to avoid modifying entry
            fixedOrdering
        );
        t.ok(a.time_start > startTime);
        t.equal(a.allotted_time, 582);
        t.equal(a.allotted_time, a.remaining_time);

        // Question data has URI inside
        t.equal(a.uri, qn.uri);

        // Counts have all started at 0
        t.equal(a.lec_answered, 0);
        t.equal(a.lec_correct, 0);
        t.equal(a.practice_answered, 0);
        t.equal(a.practice_answered, 0);

        // Pass some time, then request the same question again.
        tk.travel(new Date((new Date()).getTime() + 3000));
        t.notEqual(startTime, Math.round((new Date()).getTime() / 1000) - 1);
        t.equal(JSON.parse(ls.getItem('ut:lecture0')).answerQueue.length, 1);

        return quiz.getNewQuestion({practice: false}).then(function (args) {
            var new_a = args.a;

            // No question answered, so just get the same one back.
            t.deepEqual(a.uri, new_a.uri);
            t.deepEqual(a.ordering, new_a.ordering);
            t.equal(JSON.parse(ls.getItem('ut:lecture0')).answerQueue.length, 1);
            t.equal(a.allotted_time, new_a.remaining_time + 3); //3s have passed

            // Answer it, get new question
            return quiz.setQuestionAnswer([{name: "answer", value: 0}]);
        });

    }).then(function (args) {
        return quiz.getNewQuestion({practice: false});
    }).then(function (args) {
        var a = args.a;

        t.equal(JSON.parse(ls.getItem('ut:lecture0')).answerQueue.length, 2);

        // Time has advanced
        t.equal(assignedQns[assignedQns.length - 1].time_start, a.time_start - 3);

        // Counts have gone up
        t.equal(a.lec_answered, 1);
        t.ok(a.lec_correct <= a.lec_answered);
        t.equal(a.practice_answered, 0);
        t.equal(a.practice_correct, 0);

        // Answer, get practice question
        return quiz.setQuestionAnswer([{name: "answer", value: 0}]);
    }).then(function (args) {
        return quiz.getNewQuestion({practice: true});
    }).then(function (args) {
        var a = args.a;

        t.equal(JSON.parse(ls.getItem('ut:lecture0')).answerQueue.length, 3);

        // Counts have gone up (but for question we answered)
        t.equal(a.lec_answered, 2);
        t.ok(a.lec_correct <= a.lec_answered);
        t.equal(a.practice_answered, 0);
        t.equal(a.practice_correct, 0);

        // Answer it, practice counts go up
        return quiz.setQuestionAnswer([{name: "answer", value: 0}]);
    }).then(function (args) {
        var a = args.a;

        t.equal(a.lec_answered, 3);
        t.ok(a.lec_correct <= a.lec_answered);
        t.equal(a.practice_answered, 1);
        t.ok(a.practice_correct <= a.practice_answered);

    // Fetch an online question 
    }).then(function () {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture-online'});
    }).then(function () {
        promise = quiz.getNewQuestion({practice: false});
        return aa.waitForQueue(["GET ut:question-a 0"]);

    // Returning a fail should result in another attempt
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 0', new Error("Go away"));
        return aa.waitForQueue(["GET ut:question-a 1"]);

    // Return actual promise which should get us a question
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 1', utils.utQuestions["ut:question0"]);
        return promise;
    }).then(function (args) {
        t.equal(args.qn.text, '<div>The symbol for the set of all irrational numbers is... (a)</div>');
        return quiz.setQuestionAnswer([{name: "answer", value: 0}]);

    // If we keep failing, eventually the error bubbles up.
    }).then(function () {
        promise = quiz.getNewQuestion({practice: false});
        return aa.waitForQueue(["GET ut:question-a 2"]);
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 2', new Error("Go away"));
        return aa.waitForQueue(["GET ut:question-a 3"]);
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 3', new Error("Go away"));
        return aa.waitForQueue(["GET ut:question-a 4"]);
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 4', new Error("Go away"));
        return aa.waitForQueue(["GET ut:question-a 5"]);
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 5', new Error("Go away"));
        return aa.waitForQueue(["GET ut:question-a 6"]);
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 6', new Error("Go away"));
        return aa.waitForQueue(["GET ut:question-a 7"]);
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 7', new Error("Go away"));
        return aa.waitForQueue(["GET ut:question-a 8"]);
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 8', new Error("Go away"));
        return aa.waitForQueue(["GET ut:question-a 9"]);
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 9', new Error("Go away"));
        return aa.waitForQueue(["GET ut:question-a 10"]);
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 10', new Error("Go away"));
        return aa.waitForQueue(["GET ut:question-a 11"]);
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 11', new Error("Go away"));
        return aa.waitForQueue(["GET ut:question-a 12"]);
    }).then(function (args) {
        aa.setResponse('GET ut:question-a 12', new Error("Go away now!"));
        return promise.then(function () { t.fail(); }).catch(function (err) {
            t.equal(err.message, "Go away now!");
        }).then(function () {
            return aa.waitForQueue([]);
        });

    }).then(function (args) {
        tk.reset();
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

test('_getNewQuestion_redirect', function (t) {
    var ls = new MockLocalStorage(),
        quiz = new Quiz(ls),
        utils = test_utils();

    return utils.defaultLecture(quiz).then(function (args) {
        return args;

    // Create a question that references another question
    }).then(function (args) {
        quiz.insertQuestions({
            "ut:question0": { uri: "ut:question0a", text: "Question 0a", choices: [], shuffle: [0], answer: {}},
            "ut:question1": { uri: "ut:question1a", text: "Question 1a", choices: [], shuffle: [0], answer: {}},
            "ut:question2": { uri: "ut:question2a", text: "Question 2a", choices: [], shuffle: [0], answer: {}},
        });
        return args;

    // Fetch question
    }).then(function (args) {
        return (getQn(quiz, false));

    // Should get back one of the question(x)a URIs
    }).then(function (args) {
        t.equal(args.qn.uri, args.a.uri);
        t.equal(args.qn.uri.slice(-1), "a");

    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

test('_getQuestionData', function (t) {
    var ls = new MockLocalStorage(),
        quiz = new Quiz(ls);

    // Set up localstorage with some data
    Promise.resolve().then(function (args) {
        ls.setItem("http://camel.com/", '{"s": "camel"}');
        ls.setItem("http://sausage.com/", '{"s": "sausage"}');

    // Can fetch back data
    }).then(function (qn) {
        return quiz._getQuestionData("http://sausage.com/");
    }).then(function (qn) {
        t.deepEqual(qn, {s: "sausage", uri: "http://sausage.com/"});
    }).then(function (qn) {
        return quiz._getQuestionData("http://camel.com/");
    }).then(function (qn) {
        t.deepEqual(qn, {s: "camel", uri: "http://camel.com/"});

    // Can get the same data back thanks to the last question cache
    }).then(function (qn) {
        ls.setItem("http://camel.com/", '{"s": "dromedary"}');
        ls.setItem("http://sausage.com/", '{"s": "walls"}');
    }).then(function (qn) {
        return quiz._getQuestionData("http://camel.com/", true);
    }).then(function (qn) {
        t.deepEqual(qn, {s: "camel", uri: "http://camel.com/"});

    // But not once we ask for something else
    }).then(function (qn) {
        return quiz._getQuestionData("http://sausage.com/", true);
    }).then(function (qn) {
        t.deepEqual(qn, {s: "walls", uri: "http://sausage.com/"});
    }).then(function (qn) {
        return quiz._getQuestionData("http://camel.com/", true);
    }).then(function (qn) {
        t.deepEqual(qn, {s: "dromedary", uri: "http://camel.com/"});

    // Or if we don't use the cache
    }).then(function (qn) {
        ls.setItem("http://camel.com/", '{"s": "alice"}');
        ls.setItem("http://sausage.com/", '{"s": "cumberland"}');
    }).then(function (qn) {
        return quiz._getQuestionData("http://camel.com/", false);
    }).then(function (qn) {
        t.deepEqual(qn, {s: "alice", uri: "http://camel.com/"});

    // If question suggests a new path, then the cache uses that
    }).then(function (qn) {
        ls.setItem("http://sausage.com/", '{"uri": "http://frankfurter.com/","s": "wurst"}');
    }).then(function (qn) {
        return quiz._getQuestionData("http://sausage.com/", false);
    }).then(function (qn) {
        t.deepEqual(qn, {s: "wurst", uri: "http://frankfurter.com/"});
    }).then(function (qn) {
        return quiz._getQuestionData("http://frankfurter.com/", true);
    }).then(function (qn) {
        t.deepEqual(qn, {s: "wurst", uri: "http://frankfurter.com/"});

    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

test('_setCurrentLecture', function (t) {
    var ls = new MockLocalStorage(),
        quiz = new Quiz(ls),
        utils = test_utils();

    t.ok(!quiz.isLectureSelected());
    utils.defaultLecture(quiz);
    quiz.insertTutorial('ut:tutorial0', 'UT tutorial 0', [
        {
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:lecture0t0",
            "title": "UT Lecture 0 (no answers)",
        },
        {
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:lecture1",
            "title": "UT Lecture 1 (no answers)",
        },
        {
            "answerQueue": [ { practice: true} ],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:lecture-currentpract",
            "title": "UT Lecture: Currently practicing",
        },
        {
            "answerQueue": [ { practice: false} ],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:lecture-currentreal",
            "title": "UT Lecture: Currently real",
        },
        {
            //NB: answerQueue created for us
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:lecture0t1",
            "title": "UT Lecture 0 (from tutorial 1)",
        },
    ], utils.utQuestions).then(function (args) {
        try {
            quiz.setCurrentLecture({});
            t.fail();
        } catch (err) {
            t.equal(err.message, "lecUri parameter required");
        }

        quiz.setCurrentLecture({'lecUri': 'wibble'}).then(function () { t.fail(); }).catch(function (err) {
            t.equal(err.message, "Unknown lecture: wibble");
        });

        return quiz.setCurrentLecture({'lecUri': 'ut:lecture1'});
    }).then(function (args) {
        t.ok(quiz.isLectureSelected());
        t.equal(args.continuing, false); // No previous questions allocated
        t.equal(args.lecUri, 'ut:lecture1');
        t.equal(args.lecTitle, 'UT Lecture 1 (no answers)');

    // Can fetch from other tutorials
    }).then(function (args) {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture0t1'});
    }).then(function (args) {
        t.equal(args.continuing, false); // No previous questions allocated
        t.equal(args.lecUri, 'ut:lecture0t1');
        t.equal(args.lecTitle, 'UT Lecture 0 (from tutorial 1)');

    // Continuing shows when currently in a practice or real question
    }).then(function (args) {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture-currentreal'});
    }).then(function (args) {
        t.equal(args.continuing, 'real');
        t.equal(args.lecUri, 'ut:lecture-currentreal');
        t.equal(args.lecTitle, 'UT Lecture: Currently real');
    }).then(function (args) {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture-currentpract'});
    }).then(function (args) {
        t.equal(args.continuing, 'practice');
        t.equal(args.lecUri, 'ut:lecture-currentpract');
        t.equal(args.lecTitle, 'UT Lecture: Currently practicing');

    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

test('_fetchSlides', function (t) {
    var ls = new MockLocalStorage(),
        aa = new MockAjaxApi(),
        promise,
        quiz = new Quiz(ls, aa),
        utils = test_utils();

    return quiz.insertTutorial('ut:tutorial0', 'UT tutorial 0', [
        {
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:lecture0",
            "slide_uri": "http://slide-url-for-lecture0",
            "title": "UT Lecture 0 (no answers)",
        },
        {
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:lecture1",
            "title": "UT Lecture 1 (no answers)",
        }
    ], utils.utQuestions).then(function () {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture0'});

    // Can get a URL for lecture0
    }).then(function (args) {
        promise = quiz.fetchSlides();
        return aa.waitForQueue(["GET http://slide-url-for-lecture0 0"]);
    }).then(function (args) {
        aa.setResponse('GET http://slide-url-for-lecture0 0', "<blink>hello</blink>");
        return promise;
    }).then(function (args) {
        // Returned our fake data
        t.deepEqual(args, "<blink>hello</blink>");

    // lecture1 doesn't have one
    }).then(function (args) {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture1'});
    }).then(function (args) {
        return quiz.fetchSlides().then(function () { t.fail(); }).catch(function (err) {
            t.equal(err, "tutorweb::error::No slides available!");
        });

    // Stop it and tidy up
    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

broken_test('_fetchReview', function (t) {
    var ls = new MockLocalStorage(),
        aa = new MockAjaxApi(),
        promise,
        quiz = new Quiz(ls, aa),
        utils = test_utils();

    return quiz.insertTutorial('ut:tutorial0', 'UT tutorial 0', [
        {
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:lecture0",
            "slide_uri": "http://slide-url-for-lecture0",
            "title": "UT Lecture 0 (no review URI)",
        },
        {
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:lecture1",
            "review_uri": "http://review-url-for-lecture1",
            "title": "UT Lecture 1 (with a review)",
        }
    ], utils.utQuestions).then(function () {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture0'});

    // lecture0 doesn't have reviews
    }).then(function (args) {
        return quiz.fetchReview().then(function () { t.fail(); }).catch(function (err) {
            t.equal(err, "tutorweb::error::No review available!");
        });

    // lecture1 has a URL that can be fetched
    }).then(function (args) {
        return quiz.setCurrentLecture({'lecUri': 'ut:lecture1'});
    }).then(function (args) {
        promise = quiz.fetchReview();
        return aa.waitForQueue(["GET http://review-url-for-lecture1 0"]);
    }).then(function (args) {
        aa.setResponse('GET http://review-url-for-lecture1 0', {camels: "yes"});
        return promise;
    }).then(function (args) {
        // Returned our fake data
        t.deepEqual(args, {camels: "yes"});

    // Stop it and tidy up
    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

test('_updateAward', function (t) {
    var ls = new MockLocalStorage(),
        aa = new MockAjaxApi(),
        quiz = new Quiz(ls, aa);

    return quiz.insertTutorial('ut://tutorial0/camels/badgers/thing', 'UT tutorial 0', [
        {
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:lecture0",
            "slide_uri": "http://slide-url-for-lecture0",
            "title": "UT Lecture 0 (no answers)",
        },
    ], {}).then(function (args) {
        return args;

    // Fetch without wallet ID
    }).then(function (args) {
        var promise = quiz.updateAward(null);
        t.deepEqual(aa.getQueue(), [
            'POST /api/coin/award 0',
        ]);
        aa.setResponse('POST /api/coin/award 0', {"things": true});
        return promise;

    }).then(function (args) {
        // Returned our fake data
        t.deepEqual(args, {"things": true});
        return true;

    // Fetch with wallet ID, no captcha does the same
    }).then(function (args) {
        var promise = quiz.updateAward("WallEt");
        t.deepEqual(aa.getQueue(), [
            'POST /api/coin/award 1',
        ]);
        aa.setResponse('POST /api/coin/award 1', {"things": true});
        return promise;

    }).then(function (args) {
        // Returned our fake data
        t.deepEqual(args, {"things": true});
        return true;

    // Fetch with wallet ID and captcha
    }).then(function (args) {
        var promise = quiz.updateAward("WaLlEt", "12345");
        t.deepEqual(aa.getQueue(), [
            'POST /api/coin/award 2',
        ]);
        t.deepEqual(
            aa.data['POST /api/coin/award 2'],
            {"walletId": 'WaLlEt', captchaResponse: '12345'}
        );
        aa.setResponse('POST /api/coin/award 2', {"things": false});
        return promise;

    }).then(function (args) {
        // Returned our fake data
        t.deepEqual(args, {"things": false});
        return true;

    // Stop it and tidy up
    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

broken_test('_updateUserDetails', function (t) {
    var ls = new MockLocalStorage(),
        aa = new MockAjaxApi(),
        quiz = new Quiz(ls, aa);

    return quiz.insertTutorial('ut://tutorial0/camels/badgers/thing', 'UT tutorial 0', [
        {
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:lecture0",
            "slide_uri": "http://slide-url-for-lecture0",
            "title": "UT Lecture 0 (no answers)",
        },
    ], {}).then(function (args) {
        return args;

    // Fetch without data
    }).then(function (args) {
        var promise = quiz.updateUserDetails('ut://tutorial0/', null);
        t.deepEqual(aa.getQueue(), [
            'POST ut://tutorial0/@@quizdb-student-updatedetails 0',
        ]);
        aa.setResponse('POST ut://tutorial0/@@quizdb-student-updatedetails 0', {"things": true});
        return promise;

    }).then(function (args) {
        // Returned our fake data
        t.deepEqual(args, {"things": true});
        return true;

    // Fetch with data
    }).then(function (args) {
        var promise = quiz.updateUserDetails('ut://tutorial0/', {email: "bob@geldof.com"});
        t.deepEqual(aa.getQueue(), [
            'POST ut://tutorial0/@@quizdb-student-updatedetails 1',
        ]);
        t.deepEqual(
            aa.data['POST ut://tutorial0/@@quizdb-student-updatedetails 1'],
            {email: "bob@geldof.com"}
        );
        aa.setResponse('POST ut://tutorial0/@@quizdb-student-updatedetails 1', {"things": false});
        return promise;

    }).then(function (args) {
        // Returned our fake data
        t.deepEqual(args, {"things": false});
        return true;

    // Stop it and tidy up
    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});

// Test upgrading from old _index localstorage
broken_test('_syncSubscriptions_upgrade', function (t) {
    var ls = new MockLocalStorage(),
        aa = new MockAjaxApi(),
        quiz = new Quiz(ls, aa),
        progress = [];

    function logProgress(opTotal, opSucceeded, message) {
        progress.push({
            opTotal: opTotal,
            opSucceeded: opSucceeded,
            message: message,
        });
    }

    // Set up a bunch of work with old structure
    ls.setItem('ut:tutorial0', JSON.stringify({ title: "My first tutorial", lectures: [
        {
            "answerQueue": [{
                "time_end": 5,
                "camel" : 3,
                "lec_answered": 8,
                "lec_correct": 3,
                "practice_answered": 0,
                "practice_correct": 0,
                "synced" : false,
            }],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:t0lecture0",
            "slide_uri": "http://slide-url-for-lecture0",
            "title": "UT Lecture 0",
        },
        {
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:t0lecture1",
            "slide_uri": "http://slide-url-for-lecture0",
            "title": "UT Lecture 1",
        },
    ]}));
    ls.setItem('ut:tutorial1', JSON.stringify({ title: "My second tutorial", lectures: [
        {
            "answerQueue": [],
            "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
            "settings": {},
            "uri": "ut:t1lectureA",
            "slide_uri": "http://slide-url-for-lecture0",
            "title": "UT Lecture A",
        },
    ]}));
    ls.setItem('_index', JSON.stringify({ 'ut:tutorial0': 1, 'ut:tutorial1': 1 }));
    t.deepEqual(Object.keys(ls.obj), [
        'ut:tutorial0',
        'ut:tutorial1',
        '_index'
    ]);

    Promise.resolve().then(function () {
        var promise = quiz.syncSubscriptions({}, logProgress);

        return aa.waitForQueue(["POST /@@quizdb-subscriptions 0"]).then(function () {
            // The LS structure only has lectures at this point
            t.deepEqual(Object.keys(ls.obj), [
                'ut:t0lecture0',
                'ut:t0lecture1',
                'ut:t1lectureA',
            ]);
            // Requesting all our lectures to be added
            t.deepEqual(aa.data["POST /@@quizdb-subscriptions 0"], {
                add_lec: ['ut:t0lecture0', 'ut:t0lecture1', 'ut:t1lectureA'],
            });

            aa.setResponse("POST /@@quizdb-subscriptions 0", { children: [
                { title: "UT Tutorial 0", children: [
                    { uri: "ut:t0lecture0", "title": "UT Lecture 0" },
                    { uri: "ut:t0lecture1", "title": "UT Lecture 1" },
                ] },
                { title: "UT Tutorial 1", children: [
                    { uri: "ut:t1lectureA", "title": "UT Lecture A" },
                ] },
            ]});

        // Since there was something in t0l0's answer queue, a sync is attempted
        }).then(function () {
            return aa.waitForQueue(["POST ut:t0lecture0 1"]);
        }).then(function () {
            aa.setResponse("POST ut:t0lecture0 1", {
                "answerQueue": [{
                    "time_end": 5,
                    "camel" : 3,
                    "lec_answered": 8,
                    "lec_correct": 3,
                    "practice_answered": 0,
                    "practice_correct": 0,
                    "synced" : true,
                }],
                "questions": [ {"uri": "ut:question0", "chosen": 20, "correct": 100} ],
                "settings": {},
                "uri": "ut:t0lecture0",
                "slide_uri": "http://slide-url-for-lecture0",
                "title": "UT Lecture 0",
            });

            // Let the whole thing finish
        }).then(function () {
            return aa.waitForQueue(["GET ut:question0 2"]);
        }).then(function () {
            aa.setResponse("GET ut:question0 2", { text: "Question data" });
            return promise;
        });
    }).then(function (args) {
        // Progress was recorded for prosperity
        t.deepEqual(progress, [
            { opTotal: 3, opSucceeded: 0, message: 'Syncing subscriptions...' },
            { opTotal: 4, opSucceeded: 0, message: 'ut:t0lecture0: Fetching lecture...' },
            { opTotal: 4, opSucceeded: 0, message: 'ut:t0lecture0: Fetching questions...' },
            { opTotal: 4, opSucceeded: 0, message: 'ut:t0lecture0: Fetching questions... (1/4)' },
            { opTotal: 4, opSucceeded: 0, message: 'ut:t0lecture0: Tidying up...' },
            { opTotal: 4, opSucceeded: 1, message: 'ut:t0lecture0: Done' },
            { opTotal: 3, opSucceeded: 4, message: 'Tidying up...' },
            { opTotal: 4, opSucceeded: 4, message: 'Done' },
        ]);

        // Now have a new-style LS
        t.deepEqual(Object.keys(ls.obj), [
            'ut:t0lecture0',
            'ut:t0lecture1',
            'ut:t1lectureA',
            '_subscriptions',
            'ut:question0',
        ]);

    // Stop it and tidy up
    }).then(function (args) {
        t.end();
    }).catch(function (err) {
        console.log(err.stack);
        t.fail(err);
        t.end();
    });
});
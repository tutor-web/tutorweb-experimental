/*jslint nomen: true, plusplus: true, browser:true, regexp: true, todo: true */
/*global module, Promise */
"use strict";

module.exports['terms-display'] = function () {
    this.jqQuiz[0].innerHTML = [
        '<h3>Tutor-web Terms and Conditions</h3>',
        '<p>I agree that my grades can be recorded into a database, these can be viewed by instructors in the appropriate courses and the grades can be used anonymously for research purposes.</p>',
        '<p>Your e-mail address is collected for administrative purposes only, and will not be used as part of any research.</p>',
    ].join("\n");
    this.updateActions(['gohome', 'terms-accept']);
};

module.exports['terms-accept'] = function () {
    return this.ajaxApi.postJson('/api/student/accept-terms', {}).then(function (data) {
        // Successful, go back to start.
        if (data.success === true) {
            return 'initial';
        }
        throw new Error("Unknown response from server");
    });
};

module.exports.extend = function (twView) {
    twView.states['terms-display'] = module.exports['terms-display'];
    twView.states['terms-accept'] = module.exports['terms-accept'];

    twView.locale['terms-display'] = "Display terms and conditions";
    twView.locale['terms-accept'] = "Accept terms";
};
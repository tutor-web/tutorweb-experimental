"use strict";
/*jslint todo: true, regexp: true, nomen: true */

module.exports.parse_qs = function (location) {
    var out = {};

    if (location.pathname) {
        out._doc = location.pathname.replace(/^.*\//, '');
    }

    [].concat(
        (location.search || '').replace(/^\?/, '').split(/;|&/),
        (location.hash || '').replace(/^\#!?/, '').split(/;|&/)
    ).filter(function (str) {
        // Remove empty entries from an empty search/hash
        return str.length > 0;
    }).map(function (str) {
        var m = /(.*?)\=(.*)/.exec(str);

        if (m) {
            out[m[1]] = decodeURIComponent(m[2]);
        } else {
            if (!out._args) {
                out._args = [];
            }
            out._args.push(str);
        }
    });
    return out;
};


module.exports.parse_url = function (url_string) {
    var i,
        parts = url_string.split(/(\#|\?)/),
        location = { pathname: parts[0] };

    for (i = 1; i < parts.length; i += 2) {
        if (parts[i] === '#') {
            location.hash = '#' + parts[i + 1];
        } else if (parts[i] === '?') {
            location.search = '?' + parts[i + 1];
        }
    }

    return module.exports.parse_qs(location);
};

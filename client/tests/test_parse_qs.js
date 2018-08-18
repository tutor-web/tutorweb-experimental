"use strict";
var test = require('tape');

var parse_qs = require('../lib/parse_qs.js').parse_qs;

test('ParseQS', function (t) {
    // Can parse both hash and search
    function parseQS(pathname, search, hash) {
        return parse_qs({
            pathname: pathname,
            hash: hash,
            search: search
        });
    }

    // Can use ; or & as separator
    t.deepEqual(parseQS('/quiz.html', '?moo=yes;oink=bleh&baa=maybe', '#boing'), {
        _doc: "quiz.html",
        _args: ["boing"],
        moo: "yes",
        oink: "bleh",
        baa: "maybe"
    })

    // Empty search still works
    t.deepEqual(parseQS('/host:000/animal.html', '', '#camel=alice;snake=sid'), {
        _doc: "animal.html",
        camel: "alice",
        snake: "sid"
    })

    // Hash wins if both defined
    t.deepEqual(parseQS('/host:000/animal.html', '?camel=george', '#camel=alice'), {
        _doc: "animal.html",
        camel: "alice",
    })

    // Strings decoded
    t.deepEqual(parseQS('/host:000/animal.html', '?camel=george', '#camel=alice%20the%20camel'), {
        _doc: "animal.html",
        camel: "alice the camel",
    })

    // Can get by with just a hash
    t.deepEqual(parseQS(undefined, undefined, '#camel=alice'), {
        camel: "alice",
    })

    t.end();
});


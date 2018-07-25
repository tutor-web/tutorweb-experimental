"use strict";
/*jslint todo: true, regexp: true, browser: true */
/*global Promise */
var h = require('hyperscript');

/**
  * - orig_data: Recursive list with items of the form {children: [..inner items..], ..current item..}
  * - item_fn: Function that, given an item from the list, renders it into HTML
  */
function select_list(orig_data, item_fn) {
    var sl_el;

    function select_list_inner(data) {
        var item = item_fn(data),
            has_children = (data.children || []).length;

        return item ? h('li' + (has_children ? '.has-children' : ''), [
            item,
            has_children ? h('ul', data.children.map(select_list_inner)) : null,
        ]) : null;
    }

    function toggle(ul_el, open_close) {
        var parent_el = ul_el.parentNode;

        parent_el.classList.toggle('open', open_close);
        // NB: 3.5 is the padding around an item, count all possible items
        ul_el.style['max-height'] = parent_el.classList.contains('open') ? 3.5 * sl_el.querySelectorAll('li').length + "rem" : '';
    }

    sl_el = h('ul.select-list', {onclick: function (e) {
        var link_el = e.target,
            sibling_els = link_el.parentNode.parentNode.childNodes;

        sibling_els = Array.prototype.map.call(sibling_els, function (x) { return x.lastElementChild; });

        // Find what was clicked on
        while (link_el.nodeName !== 'A') {
            link_el = link_el.parentNode;
        }

        // If this link has a sub-list, toggle that instead of being a link
        if ((link_el.nextElementSibling || {}).nodeName === 'UL') {
            e.preventDefault();
            e.stopPropagation();

            Array.prototype.map.call(sibling_els, function (el) {
                toggle(el, link_el.nextElementSibling === el ? undefined : false);
            });
        }
    }}, (orig_data || []).map(select_list_inner));
    toggle(sl_el.querySelectorAll('ul.select-list > li:first-child > ul')[0]);

    return sl_el;
}

module.exports.select_list = select_list;

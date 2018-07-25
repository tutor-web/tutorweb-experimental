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

    function toggle(li_el, open_close) {
        var ul_el = li_el.lastElementChild;

        li_el.classList.toggle('selected', open_close);

        if (ul_el.tagName === 'UL') {
            if (li_el.classList.contains('selected')) {
                // NB: 3.5 is the padding around an item, count all possible items
                ul_el.style['max-height'] = 3.5 * sl_el.querySelectorAll('li').length + "rem";
            } else {
                // Shrink, remove selections below this item
                ul_el.style['max-height'] = '';
                Array.prototype.map.call(ul_el.querySelectorAll('.selected'), function (el) {
                    el.classList.remove('selected');
                });
            }
        }
    }

    sl_el = h('ul.select-list', {onclick: function (e) {
        var link_el = e.target;

        // Find what was clicked on
        while (link_el.nodeName !== 'A') {
            link_el = link_el.parentNode;
        }

        // Don't bother going to empty links
        if (!link_el.attributes.href || link_el.attributes.href.value === '#') {
            e.preventDefault();
            e.stopPropagation();
        }

        // Toggle all sibling list litems, we should be the only ones selected
        Array.prototype.map.call(link_el.parentNode.parentNode.childNodes, function (el) {
            toggle(el, link_el.parentNode === el ? undefined : false);
        });
    }}, (orig_data || []).map(select_list_inner));
    toggle(sl_el.querySelectorAll('ul.select-list > li:first-child')[0]);

    return sl_el;
}

module.exports.select_list = select_list;

"use strict";
/*jslint todo: true, regexp: true, browser: true, plusplus: true */
/*global Promise */
var h = require('hyperscript');

/**
  * - orig_data: Recursive list with items of the form {children: [..inner items..], ..current item..}
  * - item_fn: Function that, given an item from the list, renders it into HTML
  * - on_select: Function that is given an array of items in orig_data when something is selected
  */
function select_list(orig_data, item_fn, on_select) {
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
        var ul_el;

        if (!li_el) {
            // Recursed too deep, ignore
            return;
        }
        li_el.classList.toggle('selected', open_close);

        ul_el = li_el.lastElementChild;
        if (ul_el.tagName === 'UL') {
            if (li_el.classList.contains('selected')) {
                // NB: 3.5 is the padding around an item, count all possible items
                ul_el.style['max-height'] = 3.5 * sl_el.querySelectorAll('li').length + "rem";
            } else {
                // Shrink, remove selections below this item
                ul_el.style['max-height'] = '';
                toggle(ul_el.querySelector('.selected'), false);
            }
        }
    }

    function selected_items(data, el) {
        var i, child_els = el.childNodes;

        for (i = 0; i < data.length; i++) {
            if (child_els[i].classList.contains('selected')) {
                // This item is selected, return an array with this concatenated to everything selected within
                return [data[i]].concat(selected_items(
                    data[i].children || [],
                    child_els[i].lastElementChild
                ));
            }
        }
        return [];
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

        if (on_select) {
            on_select(selected_items(orig_data, sl_el));
        }
    }}, (orig_data || []).map(select_list_inner));
    toggle(sl_el.querySelectorAll('ul.select-list > li:first-child')[0]);
    if (on_select) {
        on_select(selected_items(orig_data, sl_el));
    }

    return sl_el;
}

module.exports.select_list = select_list;

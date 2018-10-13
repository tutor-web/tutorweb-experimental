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

    function select_list_inner(data, i) {
        var item = item_fn(data),
            has_children = (data.children || []).length;

        return item ? h('li' + (has_children ? '.has-children' : ''), { 'data-dataindex': i }, [
            item,
            has_children ? h('ul', data.children.map(select_list_inner)) : null,
        ]) : null;
    }

    function toggle(li_el, open_close, no_recurse) {
        var ul_el;

        li_el.classList.toggle('selected', open_close);

        ul_el = li_el.lastElementChild;
        if (ul_el.tagName === 'UL') {
            if (li_el.classList.contains('selected')) {
                // NB: 3.5 is the padding around an item, count all possible items
                ul_el.style['max-height'] = 3.5 * sl_el.querySelectorAll('li').length + "rem";
            } else {
                // Shrink, remove selections below this item
                ul_el.style['max-height'] = '';

                if (!no_recurse) {
                    // NB: QSA will recurse for us, so block further recursion
                    Array.prototype.map.call(ul_el.querySelectorAll('.selected'), function (el) {
                        toggle(el, false, true);
                    });
                }
            }
        }
    }

    function selected_items(data, el) {
        var i, data_index, child_els = el.childNodes;
        if (el.tagName !== "UL") {
            return [];  // The lastElementChild wasn't a UL, stop recursion
        }

        for (i = 0; i < child_els.length; i++) {
            if (child_els[i].classList.contains('selected')) {
                data_index = parseInt(child_els[i].getAttribute('data-dataindex'), 10);
                // This item is selected, return an array with this concatenated to everything selected within
                return [data[data_index]].concat(selected_items(
                    data[data_index].children || [],
                    child_els[i].lastElementChild
                ));
            }
        }
        return [];
    }

    sl_el = h('ul.select-list', {onclick: function (e) {
        var link_el = e.target;

        // Find what was clicked on
        while (link_el.nodeName !== 'LI') {
            if (link_el.nodeName === 'A' && link_el.attributes.href && link_el.attributes.href.value !== '#') {
                // We found a link to genuine content, so let defaults take hold and go to it
                return;
            }
            link_el = link_el.parentNode;

            if (!link_el || !link_el.classList || link_el.classList.contains('select-list')) {
                // Gone outside the select-list, give up.
                return;
            }
        }

        // There was no useful link clicked on, so prevent defaults
        e.preventDefault();
        e.stopPropagation();

        // Toggle all sibling list litems, we should be the only ones selected
        Array.prototype.map.call(link_el.parentNode.childNodes, function (el) {
            toggle(el, link_el === el ? undefined : false);
        });

        if (on_select) {
            on_select(selected_items(orig_data, sl_el));
        }
    }}, (orig_data || []).map(select_list_inner));

    if (sl_el.querySelector('ul.select-list > li')) {
        toggle(sl_el.querySelectorAll('ul.select-list > li:first-child')[0]);
    }

    if (on_select) {
        on_select(selected_items(orig_data, sl_el));
    }

    return sl_el;
}

module.exports.select_list = select_list;

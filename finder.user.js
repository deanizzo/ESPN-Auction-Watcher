// ==UserScript==
// @name         ESPN Draft Element Finder
// @namespace    espn-draft-watcher
// @version      1.0
// @description  Click any element on the ESPN draft page to log its selector + text, so we can build the real watcher script.
// @match        https://fantasy.espn.com/*
// @grant        none
// ==/UserScript==

(function () {
  'use strict';

  console.log(
    '%cESPN Draft Element Finder active. Hold SHIFT and click any element to log info about it.',
    'color: #16a34a; font-weight: bold;'
  );

  function cssPath(el) {
    if (!(el instanceof Element)) return '';
    const path = [];
    while (el.nodeType === Node.ELEMENT_NODE) {
      let selector = el.nodeName.toLowerCase();
      if (el.id) {
        selector += '#' + el.id;
        path.unshift(selector);
        break;
      } else {
        let sib = el, nth = 1;
        while ((sib = sib.previousElementSibling)) {
          if (sib.nodeName.toLowerCase() === selector) nth++;
        }
        if (el.className && typeof el.className === 'string') {
          selector += '.' + el.className.trim().split(/\s+/).join('.');
        }
        selector += `:nth-of-type(${nth})`;
      }
      path.unshift(selector);
      el = el.parentNode;
    }
    return path.join(' > ');
  }

  document.addEventListener(
    'click',
    (e) => {
      if (!e.shiftKey) return;
      e.preventDefault();
      e.stopPropagation();

      const el = e.target;
      console.log('%c--- Element clicked ---', 'color:#eab308;font-weight:bold;');
      console.log('Selector:', cssPath(el));
      console.log('Tag:', el.tagName, 'Classes:', el.className);
      console.log('Text content:', el.textContent.trim());
      console.log('Outer HTML:\n', el.outerHTML.slice(0, 800));
      console.log('Parent outerHTML (for context):\n', el.parentElement ? el.parentElement.outerHTML.slice(0, 1200) : 'none');
      console.log('%c------------------------', 'color:#eab308;font-weight:bold;');
    },
    true
  );
})();

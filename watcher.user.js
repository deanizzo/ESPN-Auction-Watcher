// ==UserScript==
// @name         ESPN Auction Draft Watcher
// @namespace    espn-draft-watcher
// @version      1.0
// @description  Watches the ESPN auction draft pick feed and sends each pick to a local terminal server in real time.
// @match        https://fantasy.espn.com/*
// @grant        none
// ==/UserScript==

(function () {
  'use strict';

  const SERVER_URL = 'http://localhost:3789/pick';
  const PROCESSED_ATTR = 'data-watcher-processed';

  function sendPick(pick) {
    fetch(SERVER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pick),
    }).catch((err) => {
      console.warn('[Draft Watcher] Could not reach local server. Is `node server.js` running?', err);
    });
  }

  function extractPick(li) {
    const player = li.querySelector('.playerinfo__playername');
    const nflTeam = li.querySelector('.playerinfo__playerteam');
    const pos = li.querySelector('.playerinfo__playerpos');
    const pickInfo = li.querySelector('.pick-info');

    if (!player || !pickInfo) return null;

    // pick-info text looks like: "$1 - Steez Spoke Pipeline"
    const infoText = pickInfo.textContent.trim();
    const match = infoText.match(/\$(\d+)\s*-\s*(.+)/);

    return {
      player: player.textContent.trim(),
      nflTeam: nflTeam ? nflTeam.textContent.trim() : null,
      position: pos ? pos.textContent.trim() : null,
      amount: match ? Number(match[1]) : null,
      owner: match ? match[2].trim() : null,
      // "team" field kept for server.js display formatting: NFL team + position
      team: [nflTeam ? nflTeam.textContent.trim() : '', pos ? pos.textContent.trim() : '']
        .filter(Boolean)
        .join(' '),
    };
  }

  function processLi(li) {
    if (li.hasAttribute(PROCESSED_ATTR)) return;
    li.setAttribute(PROCESSED_ATTR, 'true');

    const pick = extractPick(li);
    if (pick && pick.player) {
      sendPick(pick);
    }
  }

  function scanAndMarkExisting() {
    // On load / refresh, mark whatever picks already exist as "seen"
    // so we don't resend the whole draft history — only new picks from here on.
    document.querySelectorAll('li.pick-message__container').forEach((li) => {
      li.setAttribute(PROCESSED_ATTR, 'true');
    });
  }

  function scanForNew(root) {
    if (root.matches && root.matches('li.pick-message__container')) {
      processLi(root);
    }
    if (root.querySelectorAll) {
      root.querySelectorAll('li.pick-message__container').forEach(processLi);
    }
  }

  function extractNominee() {
    const container = document.querySelector('[data-testid="player-selected"]');
    if (!container) return null;

    const player = container.querySelector('.playerinfo__playername');
    const nflTeam = container.querySelector('.playerinfo__playerteam');
    const pos = container.querySelector('.playerinfo__playerpos');

    if (!player) return null;

    return {
      player: player.textContent.trim(),
      nflTeam: nflTeam ? nflTeam.textContent.trim() : null,
      position: pos ? pos.textContent.trim() : null,
    };
  }

  let lastNominee = null;

  function checkNominee() {
    const nominee = extractNominee();
    if (!nominee) return;

    const key = nominee.player + nominee.nflTeam + nominee.position;
    if (key === lastNominee) return; // no change
    lastNominee = key;

    fetch('http://localhost:3789/nominee', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(nominee),
    }).catch((err) => {
      console.warn('[Draft Watcher] Could not reach local server for nominee update.', err);
    });
  }

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType !== Node.ELEMENT_NODE) return;
        scanForNew(node);
      });
    }
    checkNominee();
  });

  function init() {
    scanAndMarkExisting();
    observer.observe(document.body, { childList: true, subtree: true });
    checkNominee();
    console.log(
      '%c[Draft Watcher] Active — watching for new picks, sending to http://localhost:3789',
      'color:#16a34a;font-weight:bold;'
    );
  }

  // The draft room loads content dynamically, so wait a moment before the
  // first scan in case the feed isn't mounted yet.
  if (document.readyState === 'complete') {
    setTimeout(init, 1500);
  } else {
    window.addEventListener('load', () => setTimeout(init, 1500));
  }
})();
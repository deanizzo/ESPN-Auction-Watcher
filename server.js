/**
 * ESPN Auction Draft Watcher — local server
 * ------------------------------------------
 * Run this with:  node server.js
 * Then open your ESPN draft room tab with the Tampermonkey userscript
 * installed (see finder.user.js and watcher.user.js). Picks will print
 * here live as they happen.
 *
 * No external dependencies required — just Node.js.
 */

const http = require('http');
const readline = require('readline');

const PORT = 3789;

// ---- League settings ----
const STARTING_BUDGET = 200;
const ROSTER_SPOTS = 16; // total spots per team, including bench/IR

// ANSI colors for nicer terminal output
const c = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
  gray: '\x1b[90m',
};

let pickCount = 0;
const teams = {}; // owner -> { spent, picks }
const sseClients = []; // response objects of connected SSE listeners

function broadcast(event) {
  const payload = `data: ${JSON.stringify(event)}\n\n`;
  sseClients.forEach((res) => res.write(payload));
}

function getTeam(owner) {
  if (!teams[owner]) teams[owner] = { spent: 0, picks: 0 };
  return teams[owner];
}

function teamStats(owner) {
  const t = getTeam(owner);
  const remaining = STARTING_BUDGET - t.spent;
  const spotsLeft = ROSTER_SPOTS - t.picks;
  // Must reserve at least $1 for every other open spot besides the one
  // being bid on right now.
  const maxBid = spotsLeft > 0 ? Math.max(0, remaining - (spotsLeft - 1)) : 0;
  return { ...t, remaining, spotsLeft, maxBid };
}

function printNominee(nominee) {
  const player = nominee.player || 'Unknown Player';
  const team = [nominee.nflTeam, nominee.position].filter(Boolean).join(' ');
  console.log(
    `\n${c.bold}${c.yellow}>>> NOW NOMINATED: ${player}${c.reset}${team ? ` ${c.gray}(${team})${c.reset}` : ''}\n`
  );
  broadcast({ type: 'nominee', player, nflTeam: nominee.nflTeam, position: nominee.position });
}

function printPick(pick) {
  pickCount++;
  const time = new Date().toLocaleTimeString();
  const player = pick.player || 'Unknown Player';
  const team = pick.team || 'Unknown Team';
  const amount = pick.amount != null ? Number(pick.amount) : null;
  const owner = pick.owner || 'Unknown Owner';

  console.log(
    `${c.gray}[${time}] ${c.reset}${c.bold}#${pickCount}${c.reset}  ` +
    `${c.cyan}${player}${c.reset}${team ? ` ${c.gray}(${team})${c.reset}` : ''}  ` +
    `${c.green}$${amount != null ? amount : '?'}${c.reset}  ${c.magenta}→ ${owner}${c.reset}`
  );

  if (owner !== 'Unknown Owner' && amount != null) {
    const t = getTeam(owner);
    t.spent += amount;
    t.picks += 1;

    const stats = teamStats(owner);
    console.log(
      `${c.gray}      ${owner}: ${c.reset}$${stats.remaining} left, ` +
      `${stats.spotsLeft} spots open, ${c.yellow}max bid $${stats.maxBid}${c.reset}`
    );

    broadcast({
      type: 'pick',
      pickNumber: pickCount,
      player,
      team,
      amount,
      owner,
      stats, // { spent, picks, remaining, spotsLeft, maxBid }
    });
  } else {
    broadcast({ type: 'pick', pickNumber: pickCount, player, team, amount, owner });
  }
}

function printTable() {
  const rows = Object.keys(teams)
    .sort((a, b) => teamStats(b).remaining - teamStats(a).remaining)
    .map((owner) => {
      const s = teamStats(owner);
      return {
        Owner: owner,
        Spent: `$${s.spent}`,
        Remaining: `$${s.remaining}`,
        'Spots Left': s.spotsLeft,
        'Max Bid': `$${s.maxBid}`,
      };
    });
  console.log(`\n${c.bold}${c.cyan}--- Budget Table ---${c.reset}`);
  if (rows.length === 0) {
    console.log('(no picks yet)');
  } else {
    console.table(rows);
  }
  console.log('');
}

const server = http.createServer((req, res) => {
  // CORS so the page (fantasy.espn.com) can POST to localhost
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  // Chrome's Private Network Access check: required for an HTTPS page
  // (fantasy.espn.com) to call a localhost server.
  res.setHeader('Access-Control-Allow-Private-Network', 'true');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    return res.end();
  }

  if (req.method === 'POST' && req.url === '/pick') {
    let body = '';
    req.on('data', (chunk) => (body += chunk));
    req.on('end', () => {
      try {
        const pick = JSON.parse(body);
        printPick(pick);
      } catch (e) {
        console.error('Bad payload:', body);
      }
      res.writeHead(200);
      res.end('ok');
    });
    return;
  }

  if (req.method === 'POST' && req.url === '/nominee') {
    let body = '';
    req.on('data', (chunk) => (body += chunk));
    req.on('end', () => {
      try {
        const nominee = JSON.parse(body);
        printNominee(nominee);
      } catch (e) {
        console.error('Bad nominee payload:', body);
      }
      res.writeHead(200);
      res.end('ok');
    });
    return;
  }

  if (req.method === 'GET' && req.url === '/stream') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    });
    res.write('\n'); // open the stream
    sseClients.push(res);
    console.log(`${c.gray}[stream] client connected (${sseClients.length} total)${c.reset}`);

    req.on('close', () => {
      const i = sseClients.indexOf(res);
      if (i !== -1) sseClients.splice(i, 1);
      console.log(`${c.gray}[stream] client disconnected (${sseClients.length} total)${c.reset}`);
    });
    return;
  }

  if (req.method === 'GET' && req.url === '/budgets') {
    const out = {};
    Object.keys(teams).forEach((owner) => (out[owner] = teamStats(owner)));
    res.setHeader('Content-Type', 'application/json');
    res.writeHead(200);
    return res.end(JSON.stringify(out, null, 2));
  }

  res.writeHead(404);
  res.end();
});

server.listen(PORT, () => {
  console.log(`${c.bold}${c.green}ESPN Draft Watcher server running${c.reset}`);
  console.log(`Listening on http://localhost:${PORT}`);
  console.log(`Settings: $${STARTING_BUDGET} budget, ${ROSTER_SPOTS} roster spots per team`);
  console.log(`Type "b" + Enter any time to print the full budget table.`);
  console.log(`Waiting for picks...\n`);
});

// --- Interactive commands ---
const rl = readline.createInterface({ input: process.stdin });
rl.on('line', (line) => {
  const cmd = line.trim().toLowerCase();
  if (cmd === 'b' || cmd === 'budgets' || cmd === 'table') {
    printTable();
  }
});
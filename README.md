# ESPN Auction Draft Watcher — Setup

This gets live pick data (player, price, winning owner) printing to your terminal
as your ESPN auction draft happens.

Because ESPN's API doesn't expose live draft results we have to use the javascript of the ESPN webpage to find live results and manually send them to our server. This is done through two scripts, server.js and watcher.user.js.

In the case of ESPN changing their webpage (for example UI changes), the code may break, so finder.user.js can be used for corrections.

## Step 1 — Start the local server

Requires only Node.js (no installs needed).

```bash
node server.js
```

Leave this terminal window open during your draft. It listens on
`http://localhost:3789` and will print each pick as it comes in.

## Step 2 — Install Tampermonkey + the Watcher script

1. Install the [Tampermonkey](https://www.tampermonkey.net/) browser extension (Chrome/Firefox/Edge).
2. Click the Tampermonkey icon → "Create a new script" → delete the placeholder → paste in the contents of `watcher.user.js` → save (Ctrl+S).
3. Open your ESPN auction draft room in that browser tab (make sure you're logged in as usual).

This script watches the ESPN website and sends picks as they happen to sever.js while its running.

## Step 3 - Run draft_listener.py (Optional)

Node.js will print the incoming picks but if you want any additional features this python script is where you can implement them.

This script takes live pick data from server.js and allows the user to do data manipulation. My current script finds data from a csv (not commited to git) and sends the information to discord. Because the guide_values.csv is uncommited this script will not work without modification.

This is the script that allows for analysis and manipulation of the incoming data. If you are looking to make modifications to this code you should probably start here.

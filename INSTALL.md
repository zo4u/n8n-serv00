# Install n8n 2.35.7 on Serv00 free hosting

This is a reproducible recipe based on one working FreeBSD Serv00 account in September 2026, **not** an official or one-click install. Commands run over SSH as your Serv00 user. They do not replace your existing website automatically. Check [Serv00 limits](https://www.serv00.com/) and [n8n's current Node requirements](https://docs.n8n.io/hosting/installation/npm/) first. This pins n8n **2.35.7** because the asset patch matches only that npm release. Later releases need a fresh review; do not apply this patch blindly.

## 1. Inspect the host before changing it

```sh
ssh YOUR_USER@sYOUR_SERVER.serv00.com
node --version               # this installation used Node 22.22.2
python3.11 --version
npm --version
command -v node-gyp          # and: gcc, gmake, python3.11
command -v gcc; command -v gmake
quota -h; du -sh "$HOME" "$HOME/.npm" 2>/dev/null
devil port list
devil www list
crontab -l
```

The working example needed roughly **2.4 GB** under `~/n8n` after install, against a 3 GB free-tier disk limit. If you cannot leave room for SQLite, logs and backups, stop. Remove only *your own known failed installs/caches*, not other apps or `~/.n8n`. Serv00's process limit is tight: serial native builds are important. These commands assume a fresh installation at `~/n8n` and do not migrate an existing one.

## 2. Reserve the two ports and configure the website

```sh
devil port add tcp random n8n    # note the actual port printed; call it WEB_PORT
# n8n 2.35.7's internal task-runner broker uses 127.0.0.1:5679:
devil port add tcp 5679 n8n-broker
devil port list                 # confirm BOTH reservations
```

If 5679 is unavailable, stop; this version's broker could not start on this host without that reservation. Do not substitute an arbitrary port without verifying n8n's runner-broker configuration. In the Serv00 panel, configure **your own** website as an HTTPS reverse proxy to `http://127.0.0.1:WEB_PORT`. On a newly added website, the CLI form is `devil www add YOUR_SUBDOMAIN.serv00.net proxy localhost WEB_PORT` (replace both placeholders). If your site already exists, inspect its type and content first; **do not delete it just to run the command**. Change the proxy in the panel only after saving anything the old site serves. Verify with `devil www list`. The broker port is internal and must not be exposed as a web proxy.

## 3. Install the pinned version

```sh
mkdir -p "$HOME/n8n"
printf 'prefix=%s/n8n\n' "$HOME" > "$HOME/.npmrc"  # inspect/merge if .npmrc already exists
export PATH="$HOME/n8n/bin:/usr/local/bin:$PATH"
export PYTHON=/usr/local/bin/python3.11 JOBS=1 MAKEFLAGS=-j1
export NPM_CONFIG_CACHE="/tmp/npmcache-$USER"
npm install -g n8n@2.35.7 --no-audit --no-fund --omit=optional --ignore-scripts
```

`--ignore-scripts` avoids starting many native builds during npm installation; it means the required native modules must be built explicitly, next. The specific working installation used Node 22 on FreeBSD. Don't install over an existing `~/n8n` without a backup. The install can take time and may fail if quota is exhausted; check the exit code, do not infer success from a created directory.

```sh
N="$HOME/n8n/lib/node_modules/n8n/node_modules"
(cd "$N/sqlite3" && PYTHON=/usr/local/bin/python3.11 JOBS=1 MAKEFLAGS=-j1 npm run install)
(cd "$N/isolated-vm" && PYTHON=/usr/local/bin/python3.11 JOBS=1 MAKEFLAGS=-j1 node-gyp rebuild --release -j1)
ls "$N/sqlite3/build/Release/node_sqlite3.node" "$N/isolated-vm/build/Release/isolated_vm.node"
"$HOME/n8n/bin/n8n" --version       # 2.35.7
```

If `node-gyp` is missing, install the matching toolchain in your user space first; don't skip a failed build or treat `/healthz` alone as proof of a working editor. The two native build commands reflect the original install's repair, not a claim that all possible optional nodes work. Keep your install logs private and clean disposable npm cache only after validation.

## 4. Apply the version-checked EMFILE patch

n8n 2.35.7 compiles every editor asset concurrently in `dist/commands/start.js`; this instance hit Serv00's file-descriptor limit and crashed with `EMFILE`. The [patch script](patch-emfile-2.35.7.py) replaces the single upstream `Promise.all` line with batches of 40. It checks the **exact upstream SHA-256**, saves a backup, is idempotent, and refuses unexpected local changes. Run it only when n8n is stopped (on a fresh install, before first start):

```sh
# From a local checkout of this repository, upload the script to your own server:
scp patch-emfile-2.35.7.py YOUR_USER@sYOUR_SERVER.serv00.com:~/patch-emfile-2.35.7.py
ssh YOUR_USER@sYOUR_SERVER.serv00.com
python3.11 "$HOME/patch-emfile-2.35.7.py"
node --check "$HOME/n8n/lib/node_modules/n8n/dist/commands/start.js"
```

**Never run the patch on a newer n8n version or a modified file.** It will refuse those cases instead of silently overwriting changes. Reinstalling/updating n8n overwrites the patch; rerun only after confirming the version and file hash. Keep the backup of your original file until your startup works.

## 5. Make a private start script and cron keepalive

Copy [n8n-start.example.sh](n8n-start.example.sh) to `~/n8n-start.sh`. Set `YOUR_RESERVED_WEB_PORT`, your **own** HTTPS domain, and timezone (IANA format such as `Africa/Cairo`). Generate a unique key locally on the server:

```sh
openssl rand -hex 32        # copy the output into N8N_ENCRYPTION_KEY, privately
chmod 700 "$HOME/n8n-start.sh"
sh -n "$HOME/n8n-start.sh"
sh "$HOME/n8n-start.sh"
```

Never commit, paste into issues, or publish the real script or encryption key. Keep that key stable, private and backed up securely: changing/losing it can make stored credentials unreadable. The example does **not** enable unrestricted Code-node imports by default; the original account enabled them, but that weakens isolation. Avoid exposing n8n publicly before creating an owner account and confirming auth.

After the editor is working, add a cron line **without replacing other jobs** (`crontab -e`):

```cron
* * * * * /bin/sh /usr/home/YOUR_USER/n8n-start.sh >/dev/null 2>&1
```

Check `crontab -l`. The script uses `pgrep -f 'bin/n8n start'`; don't replace this with `pgrep -f 'n8n start'` because that broader text matched the cron shell itself and prevented recovery in the case study. Cron is a restart check, not a high-availability guarantee.

## 6. Verify and maintain

```sh
tail -n 60 "$HOME/logs/n8n.log"             # don't post logs without checking for secrets
curl -I "https://YOUR_SUBDOMAIN.serv00.net/"
curl -s "https://YOUR_SUBDOMAIN.serv00.net/rest/settings" | head -c 150
```

Open the HTTPS page, confirm the actual n8n editor loads, create the first owner account, then test one harmless workflow. Confirm a **subsequent** restart through cron during a planned maintenance window; don't kill a running instance with live work just to test this. Back up `~/.n8n/database.sqlite` (or your chosen database) and the encryption key securely. The case study verified editor, REST endpoint and one cron recovery, not long-term uptime. The free tier is unsuitable for heavy workloads; internal task runners have security limitations [described by n8n](https://docs.n8n.io/hosting/configuration/task-runners/). Serv00's [current terms](https://www.serv00.com/terms-of-service/) include an account-login requirement; check them and keep backups. The setup is unofficial and version-specific.

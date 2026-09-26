# n8n on Serv00: a free-tier deployment case study

A practical record of getting n8n running on Serv00's free hosting tier. This is a troubleshooting case study, **not a one-click installer**. The fixes reflect one installation of n8n 2.35.7 in September 2026. Check current n8n and Serv00 docs before following it.

> Status: the editor, REST endpoint, and a restart through cron were verified on the instance used for this case study. Long-term reliability and upgrades have not been tested.

## The constraints

| Resource | Serv00 free tier | Why it mattered |
| --- | ---: | --- |
| Disk | 3 GB | A partial npm install and caches exhausted quota. |
| System processes | 15 | Concurrent native builds failed with `EAGAIN`. |
| Memory | 512 MB | Heavy rendering does not belong on this host. |
| TCP/UDP ports | 3 | An internal broker port had to be reserved too. |

Serv00 lists these limits at https://www.serv00.com/ . Check your own account quota before changing anything.

## What we fixed

1. **Disk full during install.** Inspect disk usage and remove only known, disposable caches and the *failed* partial install. Do not run broad cleanup against other apps. Leave room for SQLite, logs, and future updates.
2. **Native npm dependencies.** Some required packages needed a working build toolchain. Rather than removing required dependencies, compile them serially. Parallel builds had hit the host's 15-process limit (`EAGAIN`). Optional dependencies were skipped where safe; required native modules were built individually.
3. **Task runner startup hang.** n8n 2.35.7's task runner broker tried to listen on `127.0.0.1:5679`. On this Serv00 instance, localhost listening still required reserving that port through the hosting panel/`devil`. Reserving it allowed startup. Keep both the public web app port and the broker port reserved while the installation needs them. Port numbers are *example-specific*: check available ports and your own setup.
4. **`EMFILE` at editor asset startup.** The host's open-file limit caused n8n's static-asset handling to fail. A local patch batched assets in groups of 40. This is a workaround for this installation, not an upstream fix. An n8n reinstall or update can overwrite it; test startup again after each upgrade. Do not copy a patch without matching the exact upstream version and code location.
5. **Process recovery.** A per-user cron entry checked the process every minute and started it via a local startup script if absent. The script also set the instance's HTTPS webhook base URL and timezone. Keep the encryption key stable and private: losing it can make stored credentials unreadable. Do not put the startup script, the encryption key, database, personal domain, or logs containing tokens in a public repository.

## Safe deployment outline

- Confirm the current hosting limits, free disk space, available ports, and other applications first.
- Reserve only the ports your n8n version and instance need; bind internal services to localhost.
- Install the selected n8n version with its needed Node.js/toolchain, keeping process concurrency low.
- Put secrets and instance-specific values in private server-side configuration. Set the public webhook base URL to the correct HTTPS domain.
- Start n8n and verify an editor page, a REST endpoint, and a test workflow or health check. Restart the process and verify cron recovers it. A 200 from `/healthz` alone does not prove the editor is usable.
- Back up the SQLite database and encryption key securely; test restore privately. Recheck all local workarounds after upgrades.

## Limits and warnings

- This approach uses **internal task runners**, which n8n says are not recommended for production due to security isolation. External runners generally need resources outside a constrained free tier. See https://docs.n8n.io/hosting/configuration/task-runners/ .
- Serv00's terms currently say an account not logged into via the panel or SSH for 90 days may be removed without recovery: https://www.serv00.com/terms-of-service/ . A forum post suggests enforcement may differ; rely on the current written terms and back up your work.
- Never commit `.env`, `~/.n8n`, SQLite, encryption keys, SSH keys, webhook secrets, or any live domain/account details without permission.
- This repository documents troubleshooting, not an official Serv00 or n8n-supported deployment. No guarantee of uptime or fit for high-load workflows.

## Further reading

- Serv00 free hosting and limits: https://www.serv00.com/
- Serv00 terms: https://www.serv00.com/terms-of-service/
- n8n task runners: https://docs.n8n.io/hosting/configuration/task-runners/
- n8n self-host installation: https://docs.n8n.io/hosting/installation/npm/

## License

Choose an open-source license before publishing code or reusable scripts. This draft includes no scripts or vendor code.

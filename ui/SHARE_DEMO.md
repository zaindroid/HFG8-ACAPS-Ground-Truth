# Share the hackathon demo

On the demo computer, with ngrok signed in:

```powershell
cd "D:\work\hack for good\hfg8-frontend\HFG8-ACAPS-Ground-Truth-v2\ui"
powershell -ExecutionPolicy Bypass -File .\scripts\start-shared-demo.ps1
```

Install the Python engine once from the repository root:

```powershell
uv venv engine/.venv --python 3.12
uv pip install --python engine/.venv/Scripts/python.exe -r engine/requirements.txt
```

The script builds the UI, starts the trust engine, demo server and ngrok tunnel, then prints the public HTTPS URL and analyst access code. It keeps the analyst code stable across restarts and stores generated engine keys locally in the ignored `.demo-state` folder. Keep the computer awake and online. ngrok's free tier shows visitors a one-time **Visit Site** screen.

The public landing page is open. Analysts enter the access code after **Login**. Experts open their individual links without that code. The five-step case stores its invitations and confirmed answers in `.demo-state/state.json` on this computer; no external messages are sent. The synthetic panel result is loaded separately in the analyst flow. Its verification button checks a local demo fingerprint.

The **Trust** and **Public ledger** tabs read the Python engine through the same HTTPS address. That engine runs ML-KEM identity protection, ML-DSA outcome signatures, browser-side encrypted answers, and a verified process hash chain. The Trust page shows the public timestamp as **pending** until its daily root is submitted to the public log. The interactive five-step case and the seeded engine records are separate synthetic datasets; neither screen claims that the local demo fingerprint is independently witnessed.

# Share the hackathon demo

On the demo computer, with ngrok signed in:

```powershell
cd "D:\work\hack for good\hfg8-frontend\HFG8-ACAPS-Ground-Truth-v2\ui"
powershell -ExecutionPolicy Bypass -File .\scripts\start-shared-demo.ps1
```

The script builds the shared demo, starts its local server and ngrok tunnel, then prints the public HTTPS URL and analyst access code. Keep the computer awake and online. ngrok's free tier shows visitors a one-time **Visit Site** screen.

The public landing page is open. Analysts enter the access code after **Login**. Experts open their individual links without that code. The demo stores invitations and confirmed answers in `.demo-state/state.json` on this computer; no external messages are sent. The synthetic panel result is loaded separately in the analyst flow. The verification button checks a local demo fingerprint; independent timestamping is not connected.

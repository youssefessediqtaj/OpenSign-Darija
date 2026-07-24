# Manual browser check

1. Start the real Docker stack and open `http://localhost:8081/app/recognition`.
2. Confirm there is no login, account, dashboard, mode, model, dataset, or external-source
   navigation.
3. Click only `Activer la caméra` and wait for detector readiness.
4. Perform a supported sign, end naturally, and observe automatic recognition, Arabic
   display, known-only speech, cooldown, and reset.
5. Perform another sign without clicking a capture action.
6. Inspect console and network: no blocking errors; no direct inference; no auth/external
   request; no raw video/image/audio/microphone body.

Record unavailable hardware, missing sign performer, or unmeasured physical timings as
`UNCONFIRMED` rather than substituting a synthetic result.

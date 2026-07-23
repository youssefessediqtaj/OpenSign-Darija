# Browser speech fallback

When service WAV playback cannot start, the active recognition loop tries
`window.speechSynthesis` with an Arabic voice (`ar-MA`, then `ar`). This is automatic
because camera activation is the originating user gesture. Browser/OS voice availability
and autoplay behavior vary.

If both paths fail, the Arabic result remains visible, `Audio indisponible` is shown, and
the optional repeat action can retry. Failure never converts a recognized result to an
error or causes duplicate automatic speech.

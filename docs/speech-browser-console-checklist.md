# Speech Browser Console Checklist

Check for:

- React errors
- autoplay promise rejections
- `HTMLMediaElement` errors
- expired signed URL handling
- CORS failures
- `speechSynthesis` or `voiceschanged` errors
- object URL leaks
- updates after component unmount
- Web Share errors

The principal speech path should leave the console clean.

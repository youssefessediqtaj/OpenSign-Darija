export function SpeechFallbackNotice({ onUseFallback }: { onUseFallback: () => void }) {
  return (
    <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">
      <p>La voix Darija n’est pas disponible. Une voix arabe du navigateur sera utilisée si vous acceptez.</p>
      <button className="mt-2 rounded-md bg-amber-900 px-3 py-2 text-white" type="button" onClick={onUseFallback}>
        Utiliser la voix du navigateur
      </button>
    </div>
  );
}

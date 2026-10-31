export function RecordedVideoPreview({
  url,
  durationSeconds,
}: {
  url: string;
  durationSeconds: number;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4" aria-labelledby="preview-title">
      <h3 id="preview-title" className="font-semibold">
        Aperçu avant envoi
      </h3>
      <video
        src={url}
        controls
        playsInline
        className="mt-3 aspect-video w-full rounded-lg bg-slate-950 object-contain"
        aria-label="Aperçu de la contribution enregistrée"
      />
      <p className="mt-2 text-sm text-slate-600">Durée : {durationSeconds.toFixed(1)} s</p>
    </section>
  );
}

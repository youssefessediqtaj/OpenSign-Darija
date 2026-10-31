import { RotateCcw } from 'lucide-react';
import { useRef } from 'react';

import { Button } from '../../../shared/ui/Button';
import type { ContributionSign, ContributionSignKey } from '../types';

export function ReferenceSignVideo({
  signs,
  selected,
  disabled,
  onSelect,
}: {
  signs: ContributionSign[];
  selected: ContributionSign;
  disabled: boolean;
  onSelect: (key: ContributionSignKey) => void;
}) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const replay = () => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = 0;
    void videoRef.current.play();
  };
  return (
    <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="reference-title">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-cedar">Signe de référence</p>
        <h2 id="reference-title" className="mt-1 text-4xl font-bold" lang="ar" dir="rtl">
          {selected.label_ar}
        </h2>
        <p className="text-sm text-slate-500">{selected.darija_transliteration}</p>
      </div>
      {selected.reference_video_approved && selected.reference_video_url ? (
        <div>
          <video
            key={selected.reference_video_identifier}
            ref={videoRef}
            controls
            muted
            playsInline
            preload="metadata"
            poster={selected.poster_url}
            className="aspect-video w-full rounded-lg bg-slate-950 object-contain"
            aria-label={`Vidéo officielle du signe ${selected.label_ar}`}
          >
            <source src={selected.reference_video_url} type="video/mp4" />
          </video>
          <Button type="button" variant="secondary" className="mt-3" onClick={replay}>
            <RotateCcw className="mr-2 inline h-4 w-4" aria-hidden="true" />
            Rejouer la référence
          </Button>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-amber-200 bg-amber-50">
          <img
            src={selected.poster_url}
            alt=""
            className="aspect-video w-full object-cover"
          />
          <p className="p-3 text-sm text-amber-900">
            La vidéo officielle reste masquée tant que sa provenance et ses droits de diffusion
            ne sont pas approuvés.
          </p>
        </div>
      )}
      <div className="rounded-lg bg-slate-50 p-4">
        <h3 className="font-semibold">Instructions</h3>
        <p className="mt-1 text-sm leading-6 text-slate-700">{selected.recording_instructions}</p>
        <p className="mt-1 text-sm text-slate-600">
          Durée attendue : {selected.expected_min_duration_seconds} à{' '}
          {selected.expected_max_duration_seconds} secondes.
        </p>
      </div>
      <fieldset disabled={disabled}>
        <legend className="font-semibold">Choisissez un mot</legend>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-5 md:grid-cols-2">
          {signs.map((sign) => (
            <label
              key={sign.key}
              className={`cursor-pointer rounded-lg border p-3 text-center ${
                selected.key === sign.key
                  ? 'border-cedar bg-teal-50 ring-2 ring-cedar'
                  : 'border-slate-200'
              }`}
            >
              <input
                type="radio"
                name="signKey"
                className="sr-only"
                checked={selected.key === sign.key}
                onChange={() => onSelect(sign.key)}
              />
              <span className="block text-2xl font-bold" lang="ar" dir="rtl">
                {sign.label_ar}
              </span>
              <span className="text-xs text-slate-500">{sign.darija_transliteration}</span>
            </label>
          ))}
        </div>
      </fieldset>
    </section>
  );
}

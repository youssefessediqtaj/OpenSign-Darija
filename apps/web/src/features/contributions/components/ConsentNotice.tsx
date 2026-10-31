import type { ContributionNotice } from '../types';

function configured(value: string): string {
  return value || 'À configurer avant l’ouverture de la collecte';
}

export function ConsentNotice({
  notice,
  checked,
  disabled,
  onChange,
}: {
  notice: ContributionNotice | null;
  checked: boolean;
  disabled: boolean;
  onChange: (checked: boolean) => void;
}) {
  if (!notice) {
    return (
      <section className="rounded-xl border border-slate-200 bg-slate-50 p-4">
        <h3 className="font-semibold">Notice d’information</h3>
        <p className="mt-2 text-sm text-slate-600">Chargement de la notice…</p>
      </section>
    );
  }
  return (
    <section className="rounded-xl border border-teal-200 bg-teal-50/70 p-4" aria-labelledby="notice-title">
      <h3 id="notice-title" className="font-semibold text-teal-950">
        {notice.title}
      </h3>
      <p className="mt-2 text-sm leading-6 text-slate-700">{notice.summary}</p>
      <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="font-semibold">Responsable</dt>
          <dd>{configured(notice.controller_name)}</dd>
        </div>
        <div>
          <dt className="font-semibold">Contact et droits</dt>
          <dd>{configured(notice.rights_request_method)}</dd>
        </div>
        <div>
          <dt className="font-semibold">Conservation</dt>
          <dd>{notice.retention_days ? `${notice.retention_days} jours` : configured('')}</dd>
        </div>
        <div>
          <dt className="font-semibold">Référence CNDP</dt>
          <dd>{configured(notice.cndp_reference)}</dd>
        </div>
      </dl>
      <details className="mt-3 rounded-lg bg-white p-3">
        <summary className="cursor-pointer font-semibold text-cedar">Lire la notice complète</summary>
        <div className="mt-3 space-y-3 text-sm leading-6 text-slate-700">
          <p>
            <strong>Adresse et contact du responsable :</strong>{' '}
            {configured(notice.controller_address)} — {configured(notice.controller_contact)}
          </p>
          <p>
            <strong>Finalité :</strong> {configured(notice.purpose)}
          </p>
          <p>
            <strong>Données obligatoires :</strong>{' '}
            {notice.collected_data.map((field) => field.name).join(', ')}.
          </p>
          <p>
            <strong>Conséquence du refus :</strong> {notice.refusal_consequence}
          </p>
          <p>
            <strong>Destinataires :</strong>{' '}
            {notice.recipient_categories.length
              ? notice.recipient_categories.join(', ')
              : configured('')}
          </p>
          <p>
            <strong>Collaborateurs modèle :</strong>{' '}
            {configured(notice.model_collaborator_sharing)}
          </p>
          <p>
            <strong>Catégorie de lieu de stockage :</strong>{' '}
            {configured(notice.storage_location_category)}
          </p>
          <p>
            <strong>Droits :</strong> {notice.rights.join(', ')}.{' '}
            {notice.consent_timestamp_source}
          </p>
          <p>
            <strong>Procédure CNDP :</strong> {configured(notice.cndp_procedure_type)} —{' '}
            {configured(notice.cndp_reference)}.
          </p>
          {notice.complete_notice.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
          <p>
            <strong>Version de la notice :</strong> {configured(notice.notice_version)}
          </p>
        </div>
      </details>
      <label className="mt-4 flex items-start gap-3 rounded-lg bg-white p-3 text-sm leading-6">
        <input
          type="checkbox"
          className="mt-1 h-5 w-5"
          checked={checked}
          disabled={disabled}
          onChange={(event) => onChange(event.target.checked)}
        />
        <span>{notice.consent_checkbox_text}</span>
      </label>
    </section>
  );
}

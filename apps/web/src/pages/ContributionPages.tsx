import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { FormEvent } from 'react';
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom';

import { Button } from '../components/Button';
import {
  REQUIRED_LANDMARK_CONSENTS,
  VIDEO_CONSENTS,
  datasetApi,
} from '../services/datasetApi';
import { useAuthStore } from '../stores/authStore';
import type { ConsentType, DatasetContribution } from '../types/api';

const checksum = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';

function statusLabel(status: DatasetContribution['status']) {
  const labels: Record<DatasetContribution['status'], string> = {
    DRAFT: 'Brouillon',
    CAPTURING: 'Capture en cours',
    READY_TO_SUBMIT: 'Pret a envoyer',
    UPLOADING: 'Upload en cours',
    SUBMITTED: 'Envoyee',
    AUTOMATIC_CHECK_FAILED: 'Qualite insuffisante',
    PENDING_LINGUIST_REVIEW: 'Validation linguistique',
    LINGUIST_REJECTED: 'Rejetee par la review linguistique',
    PENDING_ML_REVIEW: 'Validation technique',
    ML_REJECTED: 'Rejetee par la review ML',
    APPROVED: 'Approuvee',
    REVISION_REQUESTED: 'A refaire',
    REVOKED: 'Retiree',
    ARCHIVED: 'Archivee',
  };
  return labels[status];
}

function useRole(...roles: string[]) {
  const user = useAuthStore((state) => state.user);
  return Boolean(user?.roles.some((role) => roles.includes(role)));
}

export function ContributePage() {
  const campaigns = useQuery({ queryKey: ['campaigns'], queryFn: datasetApi.campaigns });
  const contributions = useQuery({ queryKey: ['my-contributions'], queryFn: datasetApi.myContributions, retry: false });
  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">Dataset marocain</p>
        <h1 className="mt-2 text-3xl font-bold">Contribuer a OpenSign Darija</h1>
        <p className="mt-3 max-w-3xl text-slate-700 dark:text-slate-200">
          Chaque contribution est volontaire. Les landmarks et la video ont des consentements separes, et les videos ne
          sont jamais publiques automatiquement.
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <Link className="min-h-11 rounded-md bg-cedar px-5 py-2.5 font-semibold text-white hover:bg-teal-800" to="/app/contribute/consent">Gerer mes consentements</Link>
        <Link className="min-h-11 rounded-md border border-cedar px-5 py-2.5 font-semibold text-cedar hover:bg-teal-50" to="/app/contribute/campaigns">Voir les campagnes</Link>
        <Link className="min-h-11 rounded-md border border-cedar px-5 py-2.5 font-semibold text-cedar hover:bg-teal-50" to="/app/contribute/history">Historique</Link>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-lg border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-xl font-semibold">Campagnes actives</h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{campaigns.data?.length ?? 0} campagne(s) disponible(s).</p>
        </section>
        <section className="rounded-lg border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-xl font-semibold">Mes contributions</h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{contributions.data?.length ?? 0} contribution(s) creee(s).</p>
        </section>
      </div>
    </section>
  );
}

export function ConsentPage() {
  const queryClient = useQueryClient();
  const templates = useQuery({ queryKey: ['consent-templates'], queryFn: datasetApi.templates });
  const consents = useQuery({ queryKey: ['my-consents'], queryFn: datasetApi.myConsents });
  const mutation = useMutation({
    mutationFn: (choices: { consent_type: ConsentType; granted: boolean }[]) =>
      datasetApi.createConsents(templates.data?.[0]?.id ?? '', choices),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['my-consents'] }),
  });
  const template = templates.data?.[0];
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const all: ConsentType[] = [...REQUIRED_LANDMARK_CONSENTS, ...VIDEO_CONSENTS, 'PUBLIC_DATASET_RELEASE'];
    mutation.mutate(all.map((type) => ({ consent_type: type, granted: formData.get(type) === 'on' })));
  };
  return (
    <section className="max-w-3xl space-y-6">
      <h1 className="text-3xl font-bold">Consentements de contribution</h1>
      <p className="text-slate-700 dark:text-slate-200">
        Aucun choix n’est precoché. Les landmarks peuvent rester sensibles car ils décrivent des mouvements corporels.
      </p>
      {template && (
        <article className="rounded-lg border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-xl font-semibold">{template.title}</h2>
          <p className="mt-2 text-sm">{template.summary}</p>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">{template.full_text}</p>
        </article>
      )}
      <form onSubmit={submit} className="space-y-3 rounded-lg border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        {[...REQUIRED_LANDMARK_CONSENTS, ...VIDEO_CONSENTS, 'PUBLIC_DATASET_RELEASE' as ConsentType].map((type) => (
          <label key={type} className="flex gap-3 rounded-md border p-3 dark:border-slate-700">
            <input name={type} type="checkbox" className="mt-1 size-5" />
            <span>
              <span className="block font-medium">{type.split('_').join(' ')}</span>
              <span className="text-sm text-slate-600 dark:text-slate-300">
                {VIDEO_CONSENTS.includes(type) ? 'Autorise la capture video privee.' : 'Consentement gere separement.'}
              </span>
            </span>
          </label>
        ))}
        <Button disabled={!template || mutation.isPending}>Enregistrer mes choix</Button>
      </form>
      <section>
        <h2 className="text-xl font-semibold">Consentements actifs</h2>
        <ul className="mt-2 space-y-2">
          {consents.data?.map((consent) => (
            <li key={consent.id} className="flex items-center justify-between gap-3 rounded-md border p-3 dark:border-slate-700">
              <span>{consent.consent_type} — {consent.granted ? 'accorde' : 'refuse/revoque'}</span>
              {consent.granted && <Button variant="secondary" onClick={() => datasetApi.revokeConsent(consent.id)}>Revoquer</Button>}
            </li>
          ))}
        </ul>
      </section>
    </section>
  );
}

export function CampaignsPage() {
  const campaigns = useQuery({ queryKey: ['campaigns'], queryFn: datasetApi.campaigns });
  return (
    <section className="space-y-5">
      <h1 className="text-3xl font-bold">Campagnes de collecte</h1>
      <div className="grid gap-4 md:grid-cols-2">
        {campaigns.data?.map((campaign) => (
          <article key={campaign.id} className="rounded-lg border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-xl font-semibold">{campaign.name}</h2>
            <p className="mt-2 text-sm">{campaign.description}</p>
            <p className="mt-3 text-sm">Objectif: {campaign.target_sign_count} signes, {campaign.target_repetitions_per_sign} repetitions.</p>
            <Link className="mt-4 inline-flex min-h-11 rounded-md bg-cedar px-5 py-2.5 font-semibold text-white hover:bg-teal-800" to={`/app/contribute/campaigns/${campaign.id}`}>Ouvrir</Link>
          </article>
        ))}
      </div>
    </section>
  );
}

export function CampaignDetailPage() {
  const { campaignId = '' } = useParams();
  const navigate = useNavigate();
  const campaign = useQuery({ queryKey: ['campaign', campaignId], queryFn: () => datasetApi.campaign(campaignId), enabled: Boolean(campaignId) });
  const signs = useQuery({ queryKey: ['campaign-signs', campaignId], queryFn: () => datasetApi.campaignSigns(campaignId), enabled: Boolean(campaignId) });
  const create = useMutation({
    mutationFn: async (campaignSignId: string) => {
      await datasetApi.createProfile().catch(() => undefined);
      return datasetApi.createContribution(campaignId, campaignSignId, false);
    },
    onSuccess: (contribution) => navigate(`/app/contribute/session/${contribution.id}`),
  });
  return (
    <section className="space-y-6">
      <h1 className="text-3xl font-bold">{campaign.data?.name ?? 'Campagne'}</h1>
      <p className="max-w-3xl text-slate-700 dark:text-slate-200">{campaign.data?.description}</p>
      <div className="grid gap-4 md:grid-cols-2">
        {signs.data?.map((item) => (
          <article key={item.id} className="rounded-lg border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-xl font-semibold">{item.sign.french_translation}</h2>
            <p className="mt-1 text-2xl" lang="ar" dir="rtl">{item.sign.darija_arabic}</p>
            <p className="text-sm">{item.sign.darija_latin}</p>
            <p className="mt-3 text-sm">{item.instruction_text}</p>
            <Button className="mt-4" onClick={() => create.mutate(item.id)} disabled={create.isPending}>
              Commencer ce signe
            </Button>
          </article>
        ))}
      </div>
    </section>
  );
}

export function ContributionSessionPage() {
  const { contributionId = '' } = useParams();
  const queryClient = useQueryClient();
  const contribution = useQuery({ queryKey: ['contribution', contributionId], queryFn: () => datasetApi.contribution(contributionId), enabled: Boolean(contributionId) });
  const add = useMutation({
    mutationFn: async () => {
      const index = (contribution.data?.recordings.length ?? 0) + 1;
      const recording = await datasetApi.addRecording(contributionId, {
        repetition_index: index,
        feature_schema_version: '1.0.0',
        duration_ms: 1800,
        source_fps: 15,
        target_frame_count: 30,
        file_size_bytes: 0,
        landmark_size_bytes: 2048,
        checksum_landmarks: checksum,
        quality_score: 0.86,
        automatic_quality_status: 'PASSED',
        metrics: [
          { metric_name: 'detected_hand_ratio', metric_value: 0.96, threshold_min: 0.35, passed: true },
          { metric_name: 'movement_score', metric_value: 0.72, threshold_min: 0.1, passed: true },
        ],
      });
      await datasetApi.uploadSession(contributionId, recording.id, false);
      await datasetApi.confirmUpload(contributionId, recording.id, {
        checksum_landmarks: checksum,
        landmark_size_bytes: 2048,
        video_size_bytes: 0,
      });
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contribution', contributionId] }),
  });
  const submit = useMutation({ mutationFn: () => datasetApi.submitContribution(contributionId), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contribution', contributionId] }) });
  const minimum = contribution.data?.campaign?.minimum_repetitions_per_submission ?? 3;
  const count = contribution.data?.recordings.length ?? 0;
  return (
    <section className="space-y-6">
      <h1 className="text-3xl font-bold">Session de contribution</h1>
      <p>Statut: {contribution.data ? statusLabel(contribution.data.status) : 'chargement'}</p>
      <p>Mode actuel: landmarks uniquement. Aucun MediaRecorder ni Blob video n’est cree sans consentement video.</p>
      <Button onClick={() => add.mutate()} disabled={add.isPending}>Capturer une repetition de test</Button>
      <p>Progression: {count} / {minimum} minimum</p>
      <ul className="space-y-2">
        {contribution.data?.recordings.map((recording) => (
          <li key={recording.id} className="rounded-md border p-3 dark:border-slate-700">
            Repetition {recording.repetition_index}: qualite {(recording.quality_score * 100).toFixed(0)} %, upload {recording.upload_confirmed_at ? 'confirme' : 'en attente'}
          </li>
        ))}
      </ul>
      <Button onClick={() => submit.mutate()} disabled={count < minimum || submit.isPending}>Envoyer la contribution</Button>
    </section>
  );
}

export function ContributionHistoryPage() {
  const contributions = useQuery({ queryKey: ['my-contributions'], queryFn: datasetApi.myContributions });
  return (
    <section className="space-y-5">
      <h1 className="text-3xl font-bold">Historique de contribution</h1>
      {contributions.data?.map((contribution) => (
        <Link key={contribution.id} to={`/app/contribute/history/${contribution.id}`} className="block rounded-lg border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          {contribution.campaign_sign?.sign.french_translation ?? 'Signe'} — {statusLabel(contribution.status)}
        </Link>
      ))}
    </section>
  );
}

export function ContributionDetailPage() {
  const { contributionId = '' } = useParams();
  const contribution = useQuery({ queryKey: ['contribution', contributionId], queryFn: () => datasetApi.contribution(contributionId), enabled: Boolean(contributionId) });
  const revoke = useMutation({ mutationFn: () => datasetApi.revokeContribution(contributionId) });
  return (
    <section className="space-y-4">
      <h1 className="text-3xl font-bold">Detail contribution</h1>
      <p>{contribution.data ? statusLabel(contribution.data.status) : 'Chargement'}</p>
      <Button variant="secondary" onClick={() => revoke.mutate()}>Retirer cette contribution</Button>
    </section>
  );
}

export function PrivacySettingsPage() {
  return <ConsentPage />;
}

function ReviewQueue({ type }: { type: 'linguistic' | 'ml' }) {
  const allowed = useRole(type === 'linguistic' ? 'LINGUIST_REVIEWER' : 'ML_REVIEWER', 'ADMIN');
  const queryClient = useQueryClient();
  const queue = useQuery({
    queryKey: [type, 'queue'],
    queryFn: type === 'linguistic' ? datasetApi.linguisticQueue : datasetApi.mlQueue,
    enabled: allowed,
  });
  const decide = useMutation({
    mutationFn: (id: string) => type === 'linguistic' ? datasetApi.linguisticDecision(id, 'APPROVED') : datasetApi.mlDecision(id, 'APPROVED'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [type, 'queue'] }),
  });
  if (!allowed) return <Navigate to="/app" replace />;
  return (
    <section className="space-y-5">
      <h1 className="text-3xl font-bold">{type === 'linguistic' ? 'Review linguistique' : 'Review ML'}</h1>
      {queue.data?.map((contribution) => (
        <article key={contribution.id} className="rounded-lg border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-xl font-semibold">{contribution.campaign_sign?.sign.french_translation ?? 'Contribution'}</h2>
          <p>{contribution.recordings.length} repetition(s), statut {statusLabel(contribution.status)}</p>
          <LandmarkReplay />
          <Button className="mt-4" onClick={() => decide.mutate(contribution.id)}>Approuver</Button>
        </article>
      ))}
    </section>
  );
}

export function LinguisticReviewPage() {
  return <ReviewQueue type="linguistic" />;
}

export function MlReviewPage() {
  return <ReviewQueue type="ml" />;
}

export function DatasetAdminPage() {
  const allowed = useRole('ML_REVIEWER', 'ADMIN');
  const queryClient = useQueryClient();
  const datasets = useQuery({ queryKey: ['datasets'], queryFn: datasetApi.datasets, enabled: allowed });
  const create = useMutation({ mutationFn: datasetApi.createDataset, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['datasets'] }) });
  const build = useMutation({ mutationFn: datasetApi.buildDataset, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['datasets'] }) });
  if (!allowed) return <Navigate to="/app" replace />;
  return (
    <section className="space-y-5">
      <h1 className="text-3xl font-bold">Versions de dataset</h1>
      <Button onClick={() => create.mutate()}>Creer une version brouillon</Button>
      {datasets.data?.map((dataset) => (
        <article key={dataset.id} className="rounded-lg border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-xl font-semibold">{dataset.name} {dataset.semantic_version}</h2>
          <p>{dataset.status}: {dataset.recording_count} enregistrement(s), {dataset.contributor_count} contributeur(s).</p>
          <Button className="mt-3" onClick={() => build.mutate(dataset.id)}>Construire le manifest</Button>
        </article>
      ))}
    </section>
  );
}

export function LandmarkReplay() {
  return (
    <div className="mt-3 rounded-md border bg-slate-950 p-3 text-white" aria-label="Visualiseur de landmarks">
      <div className="grid h-32 place-items-center rounded bg-slate-900">
        <span className="text-sm">Lecture landmarks — mains, corps, visage reduit</span>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button variant="secondary">Lecture</Button>
        <Button variant="secondary">Pause</Button>
        <Button variant="secondary">0,5x</Button>
        <Button variant="secondary">1x</Button>
        <Button variant="secondary">2x</Button>
      </div>
    </div>
  );
}

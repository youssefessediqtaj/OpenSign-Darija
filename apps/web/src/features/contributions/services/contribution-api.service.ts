import { publicApiRequest } from '../../../shared/api/client';
import { validateServerCatalog } from '../domain/contribution-words';
import type {
  ContributionFormValues,
  ContributionNotice,
  ContributionReceipt,
  ContributionSign,
  ContributionStatus,
} from '../types';

export async function loadContributionConfiguration(signal?: AbortSignal) {
  const init = { signal };
  const [status, signs, notice] = await Promise.all([
    publicApiRequest<ContributionStatus>('/api/v1/contributions/status', init),
    publicApiRequest<ContributionSign[]>('/api/v1/contributions/signs', init),
    publicApiRequest<ContributionNotice>('/api/v1/contributions/notice', init),
  ]);
  return { status, signs: validateServerCatalog(signs), notice };
}

export async function submitContribution(
  values: ContributionFormValues,
  noticeVersion: string,
  video: Blob,
): Promise<ContributionReceipt> {
  const form = new FormData();
  form.set('full_name', values.fullName.trim());
  form.set('age', values.age);
  form.set('city', values.city.trim());
  form.set('sign_key', values.signKey);
  form.set('consent_accepted', String(values.consentAccepted));
  form.set('consent_notice_version', noticeVersion);
  form.set('video', video, 'contribution.webm');
  return publicApiRequest<ContributionReceipt>('/api/v1/contributions', {
    method: 'POST',
    body: form,
  });
}

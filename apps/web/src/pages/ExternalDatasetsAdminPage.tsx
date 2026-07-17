import { useEffect, useState } from 'react';

import { Button } from '../components/Button';
import { apiRequest } from '../lib/api';

type Source = {
  code: string;
  name: string;
  provider: string;
  version: string;
  task_type: string;
  modality: string;
  license: string;
  license_status: string;
  status: string;
  label_count: number;
  source_metadata: Record<string, unknown>;
};

type Label = {
  id: string;
  original_label: string;
  normalized_label: string;
  class_code?: string | null;
  status: string;
  sample_count: number;
};

export function ExternalDatasetsAdminPage({ labelMode }: { labelMode?: 'alphabet' | 'words' }) {
  const [sources, setSources] = useState<Source[]>([]);
  const [labels, setLabels] = useState<Label[]>([]);
  const [selected, setSelected] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    void apiRequest<Source[]>('/api/v1/admin/external-datasets').then((items) => {
      setSources(items);
      const defaultSource =
        labelMode === 'alphabet' ? 'kaggle_moroccan_lsm_alphabet' : labelMode === 'words' ? 'mendeley_mosl_v1' : items[0]?.code;
      if (defaultSource) setSelected(defaultSource);
    });
  }, [labelMode]);

  useEffect(() => {
    if (!selected) return;
    void apiRequest<Label[]>(`/api/v1/admin/external-datasets/${selected}/labels`)
      .then(setLabels)
      .catch(() => setLabels([]));
  }, [selected]);

  async function audit(source: string) {
    const result = await apiRequest<{ message: string }>(`/api/v1/admin/external-datasets/${source}/audit`, {
      method: 'POST',
    });
    setMessage(result.message);
  }

  return (
    <section>
      <h1 className="text-3xl font-bold">Datasets externes</h1>
      {message && <p className="mt-3 rounded-md bg-teal-50 p-3 text-sm text-cedar">{message}</p>}
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        {sources.map((source) => (
          <article key={source.code} className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="font-semibold">{source.name}</h2>
            <dl className="mt-3 grid gap-1 text-sm">
              <div className="flex justify-between gap-4"><dt>Source</dt><dd>{source.provider}</dd></div>
              <div className="flex justify-between gap-4"><dt>Tâche</dt><dd>{source.task_type}</dd></div>
              <div className="flex justify-between gap-4"><dt>Licence</dt><dd>{source.license_status}</dd></div>
              <div className="flex justify-between gap-4"><dt>État</dt><dd>{source.status}</dd></div>
              <div className="flex justify-between gap-4"><dt>Labels</dt><dd>{source.label_count}</dd></div>
            </dl>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button type="button" variant="secondary" onClick={() => setSelected(source.code)}>
                Labels
              </Button>
              <Button type="button" onClick={() => void audit(source.code)}>
                Audit
              </Button>
            </div>
          </article>
        ))}
      </div>
      <section className="mt-8">
        <h2 className="text-xl font-semibold">Labels externes</h2>
        {labels.length === 0 ? (
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            Aucun label importé. Construisez un manifest local avant la revue.
          </p>
        ) : (
          <div className="mt-3 overflow-x-auto rounded-md border border-slate-200 dark:border-slate-800">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-100 dark:bg-slate-900">
                <tr><th className="p-2">Original</th><th className="p-2">Normalisé</th><th className="p-2">Classe</th><th className="p-2">État</th></tr>
              </thead>
              <tbody>
                {labels.map((label) => (
                  <tr key={label.id} className="border-t border-slate-200 dark:border-slate-800">
                    <td className="p-2">{label.original_label}</td>
                    <td className="p-2">{label.normalized_label}</td>
                    <td className="p-2">{label.class_code || '-'}</td>
                    <td className="p-2">{label.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  );
}

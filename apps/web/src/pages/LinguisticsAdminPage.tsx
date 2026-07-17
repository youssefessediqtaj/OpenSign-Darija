import { useEffect, useState } from 'react';

import { messagesApi } from '../features/messages/services/messages-api.service';
import type { LinguisticTemplate, SemanticConcept } from '../types/api';

export function LinguisticsAdminPage() {
  const [concepts, setConcepts] = useState<SemanticConcept[]>([]);
  const [templates, setTemplates] = useState<LinguisticTemplate[]>([]);

  useEffect(() => {
    messagesApi.concepts().then(setConcepts);
    messagesApi.templates().then(setTemplates);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Administration linguistique</h1>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Consultation du dictionnaire de demonstration. Les modifications devront passer par validation linguistique.
        </p>
      </div>
      <section className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="font-semibold">Concepts</h2>
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          {concepts.map((concept) => (
            <div key={concept.id} className="rounded-md bg-slate-50 p-3 text-sm dark:bg-slate-800">
              <p className="font-semibold">{concept.code}</p>
              <p>{concept.name_fr} · {concept.concept_type}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="rounded-md border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="font-semibold">Templates</h2>
        <div className="mt-3 grid gap-2">
          {templates.map((template) => (
            <div key={template.id} className="rounded-md bg-slate-50 p-3 text-sm dark:bg-slate-800">
              <p className="font-semibold">{template.code}</p>
              <p>{template.name_fr} · {template.risk_level} · {template.version}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

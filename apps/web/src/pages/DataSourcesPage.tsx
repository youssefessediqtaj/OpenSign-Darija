export function DataSourcesPage() {
  return (
    <section className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="text-3xl font-bold">Sources de données</h1>
      <div className="mt-6 space-y-6">
        <article className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-xl font-semibold">A Dataset for Moroccan Sign Language (MoSL)</h2>
          <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
            <dt className="font-semibold">Fournisseur</dt>
            <dd>Mendeley Data</dd>
            <dt className="font-semibold">DOI</dt>
            <dd>10.17632/23phgyt3mt.1</dd>
            <dt className="font-semibold">Licence</dt>
            <dd>CC BY 4.0</dd>
            <dt className="font-semibold">Usage</dt>
            <dd>Signes/mots isolés, audit, mappings et recherche modèle après validation.</dd>
          </dl>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
            ScienceDirect DOI 10.1016/j.dib.2025.112395 est enregistré comme référence scientifique
            du même dataset, pas comme source de données distincte.
          </p>
        </article>
        <article className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-xl font-semibold">Moroccan Sign Language LSM Alphabet Dataset</h2>
          <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
            <dt className="font-semibold">Fournisseur</dt>
            <dd>Kaggle</dd>
            <dt className="font-semibold">Identifiant</dt>
            <dd>walidlasseg/moroccan-sign-language-lsm-alphabet-dataset</dd>
            <dt className="font-semibold">Licence</dt>
            <dd>À vérifier</dd>
            <dt className="font-semibold">Usage</dt>
            <dd>Épellation alphabet seulement après vérification de licence et revue des labels.</dd>
          </dl>
        </article>
      </div>
    </section>
  );
}

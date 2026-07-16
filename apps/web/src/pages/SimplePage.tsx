export function SimplePage({ title, children }: { title: string; children: string }) {
  return (
    <section className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-bold">{title}</h1>
      <p className="mt-4 leading-8 text-slate-700 dark:text-slate-300">{children}</p>
    </section>
  );
}

import type { ContributionFormValues, ContributionNotice } from '../types';
import { ConsentNotice } from './ConsentNotice';

export function ContributionForm({
  values,
  notice,
  collectionOpen,
  onChange,
}: {
  values: ContributionFormValues;
  notice: ContributionNotice | null;
  collectionOpen: boolean;
  onChange: (values: ContributionFormValues) => void;
}) {
  const age = Number(values.age);
  const underage = values.age !== '' && Number.isFinite(age) && age < 18;
  const set = (field: keyof ContributionFormValues, value: string | boolean) => {
    onChange({ ...values, [field]: value });
  };
  return (
    <form
      className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={(event) => event.preventDefault()}
      aria-label="Informations du contributeur"
    >
      <div>
        <h2 className="text-xl font-bold">Vos informations</h2>
        <p className="mt-1 text-sm text-slate-600">
          Seules les informations nécessaires à cette contribution sont demandées.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm font-semibold sm:col-span-2">
          Nom complet
          <input
            name="fullName"
            type="text"
            autoComplete="name"
            maxLength={120}
            required
            disabled={!collectionOpen}
            value={values.fullName}
            onChange={(event) => set('fullName', event.target.value)}
            className="mt-1 block min-h-11 w-full rounded-md border border-slate-300 px-3 font-normal"
          />
        </label>
        <label className="block text-sm font-semibold">
          Âge
          <input
            name="age"
            type="number"
            inputMode="numeric"
            min={18}
            max={120}
            required
            disabled={!collectionOpen}
            value={values.age}
            onChange={(event) => set('age', event.target.value)}
            className="mt-1 block min-h-11 w-full rounded-md border border-slate-300 px-3 font-normal"
          />
        </label>
        <label className="block text-sm font-semibold">
          Ville
          <input
            name="city"
            type="text"
            autoComplete="address-level2"
            maxLength={80}
            required
            disabled={!collectionOpen}
            value={values.city}
            onChange={(event) => set('city', event.target.value)}
            className="mt-1 block min-h-11 w-full rounded-md border border-slate-300 px-3 font-normal"
          />
        </label>
      </div>
      {underage && (
        <p className="rounded-lg bg-amber-50 p-3 text-sm font-semibold text-amber-900" role="alert">
          Le programme initial est réservé aux adultes. Aucune caméra ni donnée ne sera envoyée.
        </p>
      )}
      <ConsentNotice
        notice={notice}
        checked={values.consentAccepted}
        disabled={!collectionOpen || underage}
        onChange={(checked) => set('consentAccepted', checked)}
      />
    </form>
  );
}

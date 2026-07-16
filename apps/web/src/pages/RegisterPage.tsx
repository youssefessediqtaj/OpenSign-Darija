import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { z } from 'zod';

import { Button } from '../components/Button';
import { FieldError } from '../components/FieldError';
import { authApi } from '../services/authApi';

const schema = z
  .object({
    display_name: z.string().min(2, 'Nom trop court'),
    email: z.string().email('Adresse e-mail invalide'),
    password: z.string().min(10, 'Minimum 10 caracteres'),
    password_confirm: z.string().min(10, 'Confirmation requise'),
    accepted_terms: z.boolean().refine((value) => value, 'Acceptation requise'),
  })
  .refine((data) => data.password === data.password_confirm, {
    message: 'Les mots de passe ne correspondent pas',
    path: ['password_confirm'],
  });

type RegisterForm = z.infer<typeof schema>;

export function RegisterPage() {
  const form = useForm<RegisterForm>({
    resolver: zodResolver(schema),
    defaultValues: { display_name: '', email: '', password: '', password_confirm: '', accepted_terms: false },
  });
  const mutation = useMutation({ mutationFn: authApi.register });

  return (
    <section className="mx-auto max-w-md px-4 py-12">
      <h1 className="text-3xl font-bold">Inscription</h1>
      <form
        className="mt-6 space-y-4"
        onSubmit={form.handleSubmit((values) => {
          const { accepted_terms: acceptedTerms, ...payload } = values;
          void acceptedTerms;
          mutation.mutate(payload);
        })}
        noValidate
      >
        <label className="block">
          <span className="font-medium">Nom d'affichage</span>
          <input className="mt-1 min-h-11 w-full rounded-md border border-slate-300 px-3 dark:border-slate-700 dark:bg-slate-900" {...form.register('display_name')} />
          <FieldError message={form.formState.errors.display_name?.message} />
        </label>
        <label className="block">
          <span className="font-medium">E-mail</span>
          <input className="mt-1 min-h-11 w-full rounded-md border border-slate-300 px-3 dark:border-slate-700 dark:bg-slate-900" type="email" {...form.register('email')} />
          <FieldError message={form.formState.errors.email?.message} />
        </label>
        <label className="block">
          <span className="font-medium">Mot de passe</span>
          <input className="mt-1 min-h-11 w-full rounded-md border border-slate-300 px-3 dark:border-slate-700 dark:bg-slate-900" type="password" {...form.register('password')} />
          <FieldError message={form.formState.errors.password?.message} />
        </label>
        <label className="block">
          <span className="font-medium">Confirmation du mot de passe</span>
          <input className="mt-1 min-h-11 w-full rounded-md border border-slate-300 px-3 dark:border-slate-700 dark:bg-slate-900" type="password" {...form.register('password_confirm')} />
          <FieldError message={form.formState.errors.password_confirm?.message} />
        </label>
        <label className="flex gap-3 text-sm">
          <input type="checkbox" className="mt-1 h-5 w-5" {...form.register('accepted_terms')} />
          <span>J'accepte les conditions de contribution et de confidentialite.</span>
        </label>
        <FieldError message={form.formState.errors.accepted_terms?.message} />
        {mutation.isSuccess && <p className="text-sm font-medium text-cedar">Compte cree. Vous pouvez vous connecter.</p>}
        {mutation.isError && <p className="text-sm font-medium text-coral">Creation impossible pour le moment.</p>}
        <Button className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? 'Creation...' : 'Creer le compte'}
        </Button>
      </form>
      <p className="mt-4 text-sm">
        Deja inscrit ? <Link className="font-semibold text-cedar" to="/login">Connexion</Link>
      </p>
    </section>
  );
}

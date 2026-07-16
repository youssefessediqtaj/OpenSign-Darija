import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { Link, useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { Button } from '../components/Button';
import { FieldError } from '../components/FieldError';
import { authApi } from '../services/authApi';
import { useAuthStore } from '../stores/authStore';

const schema = z.object({
  email: z.string().email('Adresse e-mail invalide'),
  password: z.string().min(1, 'Mot de passe requis'),
});

type LoginForm = z.infer<typeof schema>;

export function LoginPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((state) => state.setSession);
  const form = useForm<LoginForm>({ resolver: zodResolver(schema), defaultValues: { email: '', password: '' } });
  const mutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (tokens) => {
      setSession(tokens);
      navigate('/app');
    },
  });

  return (
    <section className="mx-auto max-w-md px-4 py-12">
      <h1 className="text-3xl font-bold">Connexion</h1>
      <form className="mt-6 space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))} noValidate>
        <label className="block">
          <span className="font-medium">E-mail</span>
          <input className="mt-1 min-h-11 w-full rounded-md border border-slate-300 px-3 dark:border-slate-700 dark:bg-slate-900" type="email" autoComplete="email" {...form.register('email')} />
          <FieldError message={form.formState.errors.email?.message} />
        </label>
        <label className="block">
          <span className="font-medium">Mot de passe</span>
          <input className="mt-1 min-h-11 w-full rounded-md border border-slate-300 px-3 dark:border-slate-700 dark:bg-slate-900" type="password" autoComplete="current-password" {...form.register('password')} />
          <FieldError message={form.formState.errors.password?.message} />
        </label>
        {mutation.isError && <p className="text-sm font-medium text-coral">Identifiants invalides ou API indisponible.</p>}
        <Button className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? 'Connexion...' : 'Se connecter'}
        </Button>
      </form>
      <p className="mt-4 text-sm">
        Pas encore de compte ? <Link className="font-semibold text-cedar" to="/register">Creer un compte</Link>
      </p>
    </section>
  );
}

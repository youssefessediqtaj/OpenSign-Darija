import { Button } from '../../../components/Button';

export function FavoriteButton({ active, onToggle }: { active: boolean; onToggle: () => void }) {
  return <Button variant="secondary" onClick={onToggle}>{active ? 'Retirer favori' : 'Favori'}</Button>;
}

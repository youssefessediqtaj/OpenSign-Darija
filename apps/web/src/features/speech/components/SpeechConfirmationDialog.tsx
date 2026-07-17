export function SpeechConfirmationDialog({
  riskLevel,
  onCancel,
  onConfirm,
}: {
  riskLevel: string;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-950" role="alertdialog">
      <p>Vérifiez le message avant de le lire à voix haute. Niveau de risque: {riskLevel}</p>
      <div className="mt-3 flex gap-2">
        <button className="rounded-md border border-red-300 px-3 py-2" type="button" onClick={onCancel}>
          Annuler
        </button>
        <button className="rounded-md bg-red-900 px-3 py-2 text-white" type="button" onClick={onConfirm}>
          Parler
        </button>
      </div>
    </div>
  );
}

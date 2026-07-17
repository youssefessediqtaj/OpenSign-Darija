export async function copyText(text: string) {
  await navigator.clipboard.writeText(text);
}

export async function shareText(text: string) {
  if ('share' in navigator) {
    await navigator.share({ text });
    return;
  }
  await copyText(text);
}

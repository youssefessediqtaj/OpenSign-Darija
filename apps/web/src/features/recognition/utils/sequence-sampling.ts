export function uniformSample<T>(items: T[], targetCount: number): T[] {
  if (targetCount <= 0) return [];
  if (items.length === 0) return [];
  if (items.length === targetCount) return [...items];
  if (items.length === 1) return Array.from({ length: targetCount }, () => items[0]);

  const lastIndex = items.length - 1;
  return Array.from({ length: targetCount }, (_, index) => {
    const sourceIndex = Math.round((index / Math.max(targetCount - 1, 1)) * lastIndex);
    return items[Math.min(sourceIndex, lastIndex)];
  });
}

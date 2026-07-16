import { apiRequest } from '../lib/api';
import type { Category, PaginatedSigns } from '../types/api';

export const signsApi = {
  list: (search: string, category: string) => {
    const params = new URLSearchParams({ page: '1', page_size: '50' });
    if (search) params.set('search', search);
    if (category) params.set('category', category);
    return apiRequest<PaginatedSigns>(`/api/v1/signs?${params.toString()}`);
  },
  categories: () => apiRequest<Category[]>('/api/v1/categories'),
};

// Use relative path so Next.js proxy handles CORS in both dev and production
const BASE = '';

function token() {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem('admin_token') ?? '';
}

function headers(extra: HeadersInit = {}): HeadersInit {
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}`, ...extra };
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { ...init, headers: headers(init.headers as HeadersInit) });
  if (res.status === 401) {
    localStorage.removeItem('admin_token');
    window.location.href = '/';
    throw new Error('Unauthorized');
  }
  return res.json() as Promise<T>;
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (username: string, password: string) =>
  req<{ ok: boolean; token?: string; error?: string }>('/api/admin/auth', {
    method: 'POST', body: JSON.stringify({ username, password }),
  });

// ── Settings ──────────────────────────────────────────────────────────────────
export const getSettings = () => req<Settings>('/api/admin/settings');
export const updateSettings = (data: Partial<Settings>) =>
  req<{ ok: boolean }>('/api/admin/settings', { method: 'POST', body: JSON.stringify(data) });

// ── Stats ─────────────────────────────────────────────────────────────────────
export const getStats = () => req<Record<string, number>>('/api/admin/stats');

// ── Questions ─────────────────────────────────────────────────────────────────
export const getQuestions = (params?: { faculty_id?: number; status?: string }) => {
  const qs = new URLSearchParams();
  if (params?.faculty_id) qs.set('faculty_id', String(params.faculty_id));
  if (params?.status) qs.set('status', params.status);
  qs.set('limit', '100');
  return req<{ questions: Question[] }>(`/api/admin/questions?${qs}`);
};

export const answerQuestion = (qid: number, answer: string) =>
  req<{ ok: boolean; error?: string }>(`/api/admin/questions/${qid}/answer`, {
    method: 'POST', body: JSON.stringify({ answer }),
  });

// ── Faculties ─────────────────────────────────────────────────────────────────
export const getFaculties = () => req<{ faculties: Faculty[] }>('/api/admin/faculties');
export const createFaculty = (data: Partial<Faculty>) =>
  req<{ ok: boolean; error?: string }>('/api/admin/faculties', { method: 'POST', body: JSON.stringify(data) });
export const updateFaculty = (id: number, data: Partial<Faculty>) =>
  req<{ ok: boolean }>(`/api/admin/faculties/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteFaculty = (id: number) =>
  req<{ ok: boolean }>(`/api/admin/faculties/${id}`, { method: 'DELETE' });

// ── Users ─────────────────────────────────────────────────────────────────────
export const getUsers = () => req<{ users: User[] }>('/api/admin/users');
export const createUser = (data: Partial<User> & { password: string }) =>
  req<{ ok: boolean; error?: string }>('/api/admin/users', { method: 'POST', body: JSON.stringify(data) });
export const deleteUser = (id: number) =>
  req<{ ok: boolean }>(`/api/admin/users/${id}`, { method: 'DELETE' });

// ── FAQ ───────────────────────────────────────────────────────────────────────
export const getFAQ = () => req<{ items: FAQItem[] }>('/api/admin/faq');
export const createFAQ = (data: Partial<FAQItem>) =>
  req<{ ok: boolean }>('/api/admin/faq', { method: 'POST', body: JSON.stringify(data) });
export const deleteFAQ = (id: number) =>
  req<{ ok: boolean }>(`/api/admin/faq/${id}`, { method: 'DELETE' });

export const getPublicFAQ = (faculty_id?: number) => {
  const qs = faculty_id ? `?faculty_id=${faculty_id}` : '';
  return fetch(`/api/faq${qs}`).then(r => r.json()) as Promise<{ items: FAQItem[] }>;
};

export const getFiles = () => req<{ files: KBFile[] }>('/api/admin/files');
export const deleteFile = (filename: string) => req<{ ok: boolean; error?: string }>(`/api/admin/files/${filename}`, { method: 'DELETE' });

export const getPublicFiles = () => fetch('/api/public/files').then(r => r.json()) as Promise<{ files: { name: string; url: string }[] }>;

// ── Service Cards ─────────────────────────────────────────────────────────────
export const getCards = (faculty_id?: number) => {
  const qs = faculty_id ? `?faculty_id=${faculty_id}` : '';
  return req<{ cards: ServiceCard[] }>(`/api/cards${qs}`);
};
export const getAdminCards = () => req<{ cards: ServiceCard[] }>('/api/admin/cards');
export const createCard = (data: Partial<ServiceCard>) =>
  req<{ ok: boolean }>('/api/admin/cards', { method: 'POST', body: JSON.stringify(data) });
export const updateCard = (id: number, data: Partial<ServiceCard>) =>
  req<{ ok: boolean }>(`/api/admin/cards/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteCard = (id: number) =>
  req<{ ok: boolean }>(`/api/admin/cards/${id}`, { method: 'DELETE' });
export const reorderCard = (id: number, direction: 'up' | 'down') =>
  req<{ ok: boolean }>(`/api/admin/cards/${id}/reorder`, { method: 'POST', body: JSON.stringify({ direction }) });

export const uploadFile = (file: File) => {
  const fd = new FormData();
  fd.append('file', file);
  return fetch(`${BASE}/api/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token()}` },
    body: fd,
  }).then(r => r.json()) as Promise<{ ok: boolean; filename?: string; pairs?: number; error?: string }>;
};


// ── Ask (Student) ─────────────────────────────────────────────────────────────
export const askQuestion = (question: string, metadata: any = {}) =>
  fetch(`/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, ...metadata }),
  }).then(r => r.json()) as Promise<{ 
    answer: string; 
    options?: string[]; 
    lang?: string; 
    category?: string;
    rate_limited?: boolean;
    wait_time?: number;
  }>;

export const askAdmin = (question: string, metadata: any = {}) =>
  fetch(`/api/ask_admin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, ...metadata }),
  }).then(r => r.json()) as Promise<{ ok: boolean; message?: string }>;

export const getStudentHistory = (tgId: string) =>
  fetch(`/api/student/history?student_telegram_id=${encodeURIComponent(tgId)}`)
    .then(r => r.json()) as Promise<{ history: HistoryItem[] }>;

export interface HistoryItem {
  id: number;
  question: string;
  answer: string | null;
  status: 'answered' | 'unanswered';
  category: string;
  lang: string;
  created_at: string;
  answered_at: string | null;
}

// ── Types ─────────────────────────────────────────────────────────────────────
export interface Question {
  id: number;
  student_id: string;
  student_username: string;
  student_name: string;
  faculty_name: string;
  question: string;
  answer: string;
  status: 'answered' | 'unanswered';
  category: string;
  lang: string;
  created_at: string;
  student_telegram_id: string;
}

export interface Faculty {
  id: number;
  name: string;
  description: string;
  telegram_group_id: string;
  telegram_group_name: string;
  is_active: boolean;
}

export interface User {
  id: number;
  full_name: string;
  phone: string;
  role: string;
  faculty_id?: number;
  faculty_name: string;
  is_active: boolean;
}

export interface FAQItem {
  id: number;
  faculty_id?: number;
  faculty_name: string;
  question: string;
  answer: string;
}

export interface KBFile {
  name: string;
  size: number;
  created_at: number;
  status: 'draft' | 'trained';
  pairs: number;
}

export interface ServiceCard {
  id: number;
  title: string;
  description: string;
  icon: string;
  link: string;
  type: 'message' | 'link' | 'tab';
  is_active: number;
  faculty_id?: number | null;
  faculty_name?: string;
  sort_order?: number;
  start_date?: string | null;
  end_date?: string | null;
  created_at?: string;
}

export interface Settings {
  bot_start_time: string;
  bot_end_time: string;
  bot_work_days: string;
  bot_offline_message: string;
  rate_limit_requests?: string;
  rate_limit_window?: string;
}


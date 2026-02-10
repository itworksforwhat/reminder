// User types
export interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// Company types
export interface Company {
  id: string;
  name: string;
  business_number: string | null;
  owner_id: string;
  created_at: string;
}

// Reminder types
export interface Reminder {
  id: string;
  company_id: string;
  title: string;
  description: string | null;
  category: string;
  deadline: string;
  original_deadline: string | null;
  completed: boolean;
  completed_at: string | null;
  priority: number;
  template_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ReminderCreate {
  title: string;
  description?: string;
  category: string;
  deadline: string;
  priority?: number;
}

export interface ReminderUpdate {
  title?: string;
  description?: string;
  category?: string;
  deadline?: string;
  completed?: boolean;
  priority?: number;
}

export interface ReminderListResponse {
  items: Reminder[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Template types
export interface TemplateItem {
  id: string;
  title: string;
  description: string | null;
  month: number | null;
  day: number | null;
  recurrence: string;
  adjust_for_holiday: boolean;
  priority: number;
  category: string;
}

export interface Template {
  id: string;
  name: string;
  description: string | null;
  category: string;
  is_system: boolean;
  items: TemplateItem[];
  created_at: string;
}

export interface TemplateApplyRequest {
  template_id: string;
  company_id: string;
  year: number;
}

export interface GeneratedReminder {
  title: string;
  category: string;
  deadline: string;
  original_deadline: string | null;
  priority: number;
  description: string | null;
}

export interface TemplateApplyResponse {
  template_name: string;
  year: number;
  generated_count: number;
  reminders: GeneratedReminder[];
}

// WebSocket types
export interface SyncMessage {
  event: 'created' | 'updated' | 'deleted' | 'bulk_created';
  entity: string;
  id: string | null;
  data: Record<string, unknown> | null;
}

// UI types
export type ViewMode = 'list' | 'calendar';
export type CalendarView = 'month' | 'week';

export const CATEGORIES = [
  '원천세', '4대보험', '부가세', '법인세', '종합소득세',
  '지방소득세', '연말정산', '급여', 'HR',
] as const;

export const PRIORITY_LABELS: Record<number, string> = {
  0: '보통',
  1: '낮음',
  2: '높음',
  3: '긴급',
};

export const PRIORITY_COLORS: Record<number, string> = {
  0: '#9e9e9e',
  1: '#4caf50',
  2: '#ff9800',
  3: '#f44336',
};

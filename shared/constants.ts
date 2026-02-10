export const API_CATEGORIES = {
  TAX: 'tax',
  PAYROLL: 'payroll',
  HR: 'hr',
} as const;

export const REMINDER_CATEGORIES = [
  '원천세', '4대보험', '부가세', '법인세', '종합소득세',
  '지방소득세', '연말정산', '급여', 'HR',
] as const;

export const PRIORITY = {
  NORMAL: 0,
  LOW: 1,
  HIGH: 2,
  URGENT: 3,
} as const;

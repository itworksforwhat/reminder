import { useState, useEffect, useCallback } from 'react';
import type { Reminder, ReminderCreate, ReminderUpdate } from '../types';
import { remindersApi } from '../services/api';
import { wsService } from '../services/websocket';
import { useAuth } from '../contexts/AuthContext';

interface UseRemindersOptions {
  page?: number;
  pageSize?: number;
  category?: string;
  completed?: boolean;
  year?: number;
  month?: number;
}

export function useReminders(options: UseRemindersOptions = {}) {
  const { company } = useAuth();
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReminders = useCallback(async () => {
    if (!company) return;

    setLoading(true);
    setError(null);

    try {
      const { data } = await remindersApi.list(company.id, {
        page: options.page,
        page_size: options.pageSize,
        category: options.category,
        completed: options.completed,
        year: options.year,
        month: options.month,
      });
      setReminders(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load reminders');
    } finally {
      setLoading(false);
    }
  }, [company, options.page, options.pageSize, options.category, options.completed, options.year, options.month]);

  useEffect(() => {
    fetchReminders();
  }, [fetchReminders]);

  // WebSocket sync
  useEffect(() => {
    const unsubscribe = wsService.onMessage((message) => {
      if (message.entity === 'reminder') {
        fetchReminders();
      }
    });
    return unsubscribe;
  }, [fetchReminders]);

  const createReminder = useCallback(async (data: ReminderCreate) => {
    if (!company) throw new Error('No company selected');
    const { data: reminder } = await remindersApi.create(company.id, data);
    await fetchReminders();
    return reminder;
  }, [company, fetchReminders]);

  const updateReminder = useCallback(async (id: string, data: ReminderUpdate) => {
    const { data: reminder } = await remindersApi.update(id, data);
    await fetchReminders();
    return reminder;
  }, [fetchReminders]);

  const deleteReminder = useCallback(async (id: string) => {
    await remindersApi.delete(id);
    await fetchReminders();
  }, [fetchReminders]);

  const toggleComplete = useCallback(async (id: string, completed: boolean) => {
    return updateReminder(id, { completed });
  }, [updateReminder]);

  return {
    reminders,
    total,
    totalPages,
    loading,
    error,
    fetchReminders,
    createReminder,
    updateReminder,
    deleteReminder,
    toggleComplete,
  };
}

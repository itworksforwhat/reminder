import React, { useState, useEffect, useCallback } from 'react';
import {
  Box, Typography, Paper, Alert, LinearProgress,
  List, ListItem, ListItemText, Chip, Divider, Button,
} from '@mui/material';
import {
  Warning as OverdueIcon,
  Today as TodayIcon,
  Schedule as UpcomingIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useAuth } from '../contexts/AuthContext';
import { notificationsApi } from '../services/api';
import { PRIORITY_LABELS, PRIORITY_COLORS } from '../types';

interface NotificationReminder {
  reminder_id: string;
  title: string;
  category: string;
  deadline: string;
  priority: number;
  d_day_label: string;
  company_id: string;
  days_overdue?: number;
  days_left?: number;
}

interface NotificationSummary {
  today: { count: number; items: NotificationReminder[] };
  overdue: { count: number; items: NotificationReminder[] };
  upcoming_7days: { count: number; items: NotificationReminder[] };
  total_pending: number;
  generated_at: string;
}

export default function NotificationsPage() {
  const { company } = useAuth();
  const [summary, setSummary] = useState<NotificationSummary | null>(null);
  const [todayItems, setTodayItems] = useState<NotificationReminder[]>([]);
  const [overdueItems, setOverdueItems] = useState<NotificationReminder[]>([]);
  const [upcomingItems, setUpcomingItems] = useState<NotificationReminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNotifications = useCallback(async () => {
    if (!company) return;
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, todayRes, overdueRes, upcomingRes] = await Promise.all([
        notificationsApi.summary(),
        notificationsApi.today(),
        notificationsApi.overdue(),
        notificationsApi.upcoming(7),
      ]);
      setSummary(summaryRes.data);
      setTodayItems(todayRes.data);
      setOverdueItems(overdueRes.data);
      setUpcomingItems(upcomingRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || '알림 정보를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, [company]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  if (!company) {
    return (
      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Alert severity="info">
          회사를 먼저 등록해주세요.
        </Alert>
      </Box>
    );
  }

  const formatDeadline = (deadline: string) => {
    try {
      return format(new Date(deadline), 'yyyy년 M월 d일 (EEE)', { locale: ko });
    } catch {
      return deadline;
    }
  };

  const renderReminderList = (
    items: NotificationReminder[],
    icon: React.ReactNode,
    title: string,
    emptyMessage: string,
    color: string,
  ) => (
    <Paper sx={{ mb: 3, overflow: 'hidden' }}>
      <Box sx={{ p: 2, bgcolor: color, color: 'white', display: 'flex', alignItems: 'center', gap: 1 }}>
        {icon}
        <Typography variant="h6" fontWeight={600}>{title}</Typography>
        <Chip label={items.length} size="small" sx={{ bgcolor: 'rgba(255,255,255,0.3)', color: 'white', ml: 1 }} />
      </Box>
      {items.length === 0 ? (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">{emptyMessage}</Typography>
        </Box>
      ) : (
        <List disablePadding>
          {items.map((item, idx) => (
            <React.Fragment key={item.reminder_id}>
              {idx > 0 && <Divider />}
              <ListItem sx={{ py: 1.5 }}>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                      <Typography fontWeight={600}>{item.title}</Typography>
                      <Chip label={item.category} size="small" variant="outlined" />
                      <Chip
                        label={PRIORITY_LABELS[item.priority] || '보통'}
                        size="small"
                        sx={{ bgcolor: PRIORITY_COLORS[item.priority] || '#9e9e9e', color: 'white' }}
                      />
                    </Box>
                  }
                  secondary={
                    <Box sx={{ display: 'flex', gap: 2, mt: 0.5 }}>
                      <Typography variant="body2" color="text.secondary">
                        {formatDeadline(item.deadline)}
                      </Typography>
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        color={
                          item.days_overdue ? 'error.main' :
                          item.d_day_label === 'D-Day' ? 'warning.main' : 'info.main'
                        }
                      >
                        {item.d_day_label}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      )}
    </Paper>
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight={700}>알림</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {summary && (
            <Typography variant="body2" color="text.secondary">
              총 미완료: {summary.total_pending}건
            </Typography>
          )}
          <Button onClick={fetchNotifications} variant="outlined" size="small">새로고침</Button>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {!loading && (
        <>
          {renderReminderList(
            overdueItems,
            <OverdueIcon />,
            '지연된 일정',
            '지연된 일정이 없습니다.',
            '#f44336',
          )}
          {renderReminderList(
            todayItems,
            <TodayIcon />,
            '오늘 마감',
            '오늘 마감인 일정이 없습니다.',
            '#ff9800',
          )}
          {renderReminderList(
            upcomingItems,
            <UpcomingIcon />,
            '7일 내 예정',
            '7일 내 예정된 일정이 없습니다.',
            '#2196f3',
          )}
        </>
      )}
    </Box>
  );
}

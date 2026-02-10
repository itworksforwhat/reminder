import React, { useState, useMemo } from 'react';
import {
  Box, Typography, Paper, Grid, Chip, IconButton,
  useTheme,
} from '@mui/material';
import {
  ChevronLeft as PrevIcon,
  ChevronRight as NextIcon,
} from '@mui/icons-material';
import {
  format, startOfMonth, endOfMonth, startOfWeek, endOfWeek,
  addDays, isSameMonth, isSameDay, isToday, addMonths, subMonths,
} from 'date-fns';
import { ko } from 'date-fns/locale';
import type { Reminder } from '../types';
import { PRIORITY_COLORS } from '../types';
import { useReminders } from '../hooks/useReminders';

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토'];

export default function CalendarPage() {
  const theme = useTheme();
  const [currentDate, setCurrentDate] = useState(new Date());
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth() + 1;

  const { reminders } = useReminders({ year, month, pageSize: 100 });

  // Build calendar grid
  const calendarDays = useMemo(() => {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const startDate = startOfWeek(monthStart, { weekStartsOn: 0 });
    const endDate = endOfWeek(monthEnd, { weekStartsOn: 0 });

    const days: Date[] = [];
    let day = startDate;
    while (day <= endDate) {
      days.push(day);
      day = addDays(day, 1);
    }
    return days;
  }, [currentDate]);

  // Group reminders by date
  const remindersByDate = useMemo(() => {
    const map: Record<string, Reminder[]> = {};
    reminders.forEach((r) => {
      const key = r.deadline;
      if (!map[key]) map[key] = [];
      map[key].push(r);
    });
    return map;
  }, [reminders]);

  return (
    <Box>
      {/* Calendar Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 3, gap: 2 }}>
        <IconButton onClick={() => setCurrentDate(subMonths(currentDate, 1))}>
          <PrevIcon />
        </IconButton>
        <Typography variant="h5" fontWeight={700}>
          {format(currentDate, 'yyyy년 M월', { locale: ko })}
        </Typography>
        <IconButton onClick={() => setCurrentDate(addMonths(currentDate, 1))}>
          <NextIcon />
        </IconButton>
      </Box>

      {/* Weekday headers */}
      <Grid container>
        {WEEKDAYS.map((day, i) => (
          <Grid item xs key={day} sx={{ textAlign: 'center', py: 1 }}>
            <Typography
              variant="body2"
              fontWeight={600}
              color={i === 0 ? 'error.main' : i === 6 ? 'primary.main' : 'text.primary'}
            >
              {day}
            </Typography>
          </Grid>
        ))}
      </Grid>

      {/* Calendar Grid */}
      <Grid container sx={{ border: 1, borderColor: 'divider' }}>
        {calendarDays.map((day, index) => {
          const dateKey = format(day, 'yyyy-MM-dd');
          const dayReminders = remindersByDate[dateKey] || [];
          const isCurrentMonth = isSameMonth(day, currentDate);
          const isWeekend = day.getDay() === 0 || day.getDay() === 6;

          return (
            <Grid
              item
              xs
              key={index}
              sx={{
                minHeight: 100,
                border: 0.5,
                borderColor: 'divider',
                bgcolor: isToday(day) ? 'action.selected' : !isCurrentMonth ? 'action.hover' : 'background.paper',
                p: 0.5,
                ...(index % 7 === 0 ? { borderLeft: 0 } : {}),
              }}
            >
              <Typography
                variant="body2"
                sx={{
                  fontWeight: isToday(day) ? 700 : 400,
                  color: !isCurrentMonth ? 'text.disabled' :
                    day.getDay() === 0 ? 'error.main' :
                    day.getDay() === 6 ? 'primary.main' : 'text.primary',
                  mb: 0.5,
                }}
              >
                {format(day, 'd')}
              </Typography>

              {dayReminders.slice(0, 3).map((r) => (
                <Chip
                  key={r.id}
                  label={r.title}
                  size="small"
                  sx={{
                    mb: 0.25,
                    width: '100%',
                    justifyContent: 'flex-start',
                    height: 20,
                    fontSize: 11,
                    bgcolor: r.completed ? '#e8f5e9' : undefined,
                    textDecoration: r.completed ? 'line-through' : 'none',
                    borderLeft: 3,
                    borderColor: PRIORITY_COLORS[r.priority] || '#9e9e9e',
                    borderRadius: 1,
                  }}
                />
              ))}
              {dayReminders.length > 3 && (
                <Typography variant="caption" color="text.secondary">
                  +{dayReminders.length - 3}건
                </Typography>
              )}
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
}

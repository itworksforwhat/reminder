import React from 'react';
import {
  Card, CardContent, Typography, Checkbox, Chip, Box,
  IconButton, Tooltip,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  Flag as FlagIcon,
} from '@mui/icons-material';
import { format, isPast, isToday, differenceInDays } from 'date-fns';
import { ko } from 'date-fns/locale';
import type { Reminder } from '../types';
import { PRIORITY_LABELS, PRIORITY_COLORS } from '../types';

interface Props {
  reminder: Reminder;
  onToggle: (id: string, completed: boolean) => void;
  onEdit: (reminder: Reminder) => void;
  onDelete: (id: string) => void;
}

export default function ReminderCard({ reminder, onToggle, onEdit, onDelete }: Props) {
  const deadline = new Date(reminder.deadline);
  const daysLeft = differenceInDays(deadline, new Date());
  const overdue = isPast(deadline) && !isToday(deadline) && !reminder.completed;
  const today = isToday(deadline);

  const getDDayLabel = () => {
    if (reminder.completed) return '완료';
    if (today) return 'D-Day';
    if (overdue) return `D+${Math.abs(daysLeft)}`;
    return `D-${daysLeft}`;
  };

  const getDDayColor = (): 'error' | 'warning' | 'success' | 'default' | 'info' => {
    if (reminder.completed) return 'success';
    if (overdue) return 'error';
    if (today) return 'error';
    if (daysLeft <= 3) return 'warning';
    if (daysLeft <= 7) return 'info';
    return 'default';
  };

  return (
    <Card
      sx={{
        mb: 1,
        opacity: reminder.completed ? 0.7 : 1,
        borderLeft: 4,
        borderColor: overdue ? 'error.main' : today ? 'warning.main' : 'primary.main',
        '&:hover': { boxShadow: 3 },
        transition: 'box-shadow 0.2s',
      }}
    >
      <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Checkbox
            checked={reminder.completed}
            onChange={() => onToggle(reminder.id, !reminder.completed)}
            size="small"
          />

          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <Typography
              variant="body1"
              sx={{
                textDecoration: reminder.completed ? 'line-through' : 'none',
                fontWeight: 500,
              }}
              noWrap
            >
              {reminder.title}
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap' }}>
              <Chip label={reminder.category} size="small" variant="outlined" />
              <Chip
                label={format(deadline, 'M/d (EEE)', { locale: ko })}
                size="small"
                color={overdue ? 'error' : 'default'}
                variant="outlined"
              />
              {reminder.original_deadline && (
                <Tooltip title={`원래 마감일: ${reminder.original_deadline}`}>
                  <Chip label="조정됨" size="small" color="info" variant="outlined" />
                </Tooltip>
              )}
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {reminder.priority > 0 && (
              <FlagIcon
                fontSize="small"
                sx={{ color: PRIORITY_COLORS[reminder.priority] }}
                titleAccess={PRIORITY_LABELS[reminder.priority]}
              />
            )}
            <Chip
              label={getDDayLabel()}
              size="small"
              color={getDDayColor()}
              sx={{ fontWeight: 600, minWidth: 56 }}
            />
            <IconButton size="small" onClick={() => onEdit(reminder)}>
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => onDelete(reminder.id)} color="error">
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

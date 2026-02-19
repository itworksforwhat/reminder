import React, { useState, useMemo } from 'react';
import {
  Box, Typography, Button, Grid, Paper, Chip, TextField,
  MenuItem, ToggleButtonGroup, ToggleButton, LinearProgress,
  IconButton, Tooltip, Alert, Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  FileDownload as ExportIcon,
  FileUpload as ImportIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { isToday, isPast } from 'date-fns';
import type { Reminder, ReminderCreate, ReminderUpdate } from '../types';
import { CATEGORIES } from '../types';
import { useReminders } from '../hooks/useReminders';
import { useAuth } from '../contexts/AuthContext';
import { remindersApi } from '../services/api';
import ReminderCard from '../components/ReminderCard';
import ReminderDialog from '../components/ReminderDialog';

export default function DashboardPage() {
  const { company } = useAuth();
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState<string>('');
  const [completedFilter, setCompletedFilter] = useState<string>('all');
  const [year] = useState(new Date().getFullYear());

  const completedValue = completedFilter === 'all' ? undefined :
    completedFilter === 'completed' ? true : false;

  const {
    reminders, total, totalPages, loading, error,
    createReminder, updateReminder, deleteReminder, toggleComplete, fetchReminders,
  } = useReminders({
    page,
    pageSize: 50,
    category: category || undefined,
    completed: completedValue,
    year,
  });

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingReminder, setEditingReminder] = useState<Reminder | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false, message: '', severity: 'success',
  });

  // Summary stats
  const stats = useMemo(() => {
    const todayItems = reminders.filter((r) => isToday(new Date(r.deadline)) && !r.completed);
    const overdue = reminders.filter((r) => isPast(new Date(r.deadline)) && !isToday(new Date(r.deadline)) && !r.completed);
    const upcoming = reminders.filter((r) => !r.completed && !isPast(new Date(r.deadline)));
    const completed = reminders.filter((r) => r.completed);
    return { todayItems, overdue, upcoming, completed };
  }, [reminders]);

  const handleSave = async (data: ReminderCreate | ReminderUpdate) => {
    if (editingReminder) {
      await updateReminder(editingReminder.id, data as ReminderUpdate);
    } else {
      await createReminder(data as ReminderCreate);
    }
  };

  const handleExport = async () => {
    if (!company) return;
    try {
      const response = await remindersApi.exportExcel(company.id, year, category || undefined);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `reminders_${year}.xlsx`;
      link.click();
      window.URL.revokeObjectURL(url);
      setSnackbar({ open: true, message: 'Excel 파일을 다운로드했습니다.', severity: 'success' });
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Excel 내보내기에 실패했습니다.';
      setSnackbar({ open: true, message, severity: 'error' });
    }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!company || !e.target.files?.[0]) return;
    try {
      await remindersApi.importExcel(company.id, e.target.files[0]);
      fetchReminders();
      setSnackbar({ open: true, message: 'Excel 파일을 가져왔습니다.', severity: 'success' });
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Excel 가져오기에 실패했습니다.';
      setSnackbar({ open: true, message, severity: 'error' });
    }
    // Reset input so the same file can be imported again
    e.target.value = '';
  };

  if (!company) {
    return (
      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Alert severity="info">
          회사를 먼저 등록해주세요. 회원가입 시 자동으로 회사를 등록할 수 있습니다.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight={700}>
          대시보드
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Excel 내보내기">
            <IconButton onClick={handleExport} color="primary">
              <ExportIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Excel 가져오기">
            <IconButton component="label" color="primary">
              <ImportIcon />
              <input type="file" hidden accept=".xlsx,.xls" onChange={handleImport} />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setEditingReminder(null);
              setDialogOpen(true);
            }}
          >
            새 일정
          </Button>
        </Box>
      </Box>

      {/* Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {[
          { label: '오늘 마감', count: stats.todayItems.length, color: '#ff9800' },
          { label: '지연', count: stats.overdue.length, color: '#f44336' },
          { label: '예정', count: stats.upcoming.length, color: '#2196f3' },
          { label: '완료', count: stats.completed.length, color: '#4caf50' },
        ].map(({ label, count, color }) => (
          <Grid item xs={6} md={3} key={label}>
            <Paper sx={{ p: 2, textAlign: 'center', borderTop: 3, borderColor: color }}>
              <Typography variant="h4" fontWeight={700} sx={{ color }}>
                {count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {label}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <FilterIcon color="action" />
        <TextField
          label="카테고리"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          select
          size="small"
          sx={{ minWidth: 140 }}
        >
          <MenuItem value="">전체</MenuItem>
          {CATEGORIES.map((cat) => (
            <MenuItem key={cat} value={cat}>{cat}</MenuItem>
          ))}
        </TextField>
        <ToggleButtonGroup
          value={completedFilter}
          exclusive
          onChange={(_, v) => v && setCompletedFilter(v)}
          size="small"
        >
          <ToggleButton value="all">전체</ToggleButton>
          <ToggleButton value="pending">미완료</ToggleButton>
          <ToggleButton value="completed">완료</ToggleButton>
        </ToggleButtonGroup>
        <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
          총 {total}건
        </Typography>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Reminder List */}
      {reminders.length === 0 && !loading ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">
            일정이 없습니다. 새 일정을 추가하거나 템플릿을 적용하세요.
          </Typography>
        </Paper>
      ) : (
        reminders.map((reminder) => (
          <ReminderCard
            key={reminder.id}
            reminder={reminder}
            onToggle={toggleComplete}
            onEdit={(r) => {
              setEditingReminder(r);
              setDialogOpen(true);
            }}
            onDelete={deleteReminder}
          />
        ))
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2, gap: 1 }}>
          <Button disabled={page <= 1} onClick={() => setPage(page - 1)}>이전</Button>
          <Chip label={`${page} / ${totalPages}`} />
          <Button disabled={page >= totalPages} onClick={() => setPage(page + 1)}>다음</Button>
        </Box>
      )}

      {/* Dialog */}
      <ReminderDialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setEditingReminder(null);
        }}
        onSave={handleSave}
        reminder={editingReminder}
      />

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

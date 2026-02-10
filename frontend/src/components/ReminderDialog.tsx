import React, { useState, useEffect } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, TextField, MenuItem, Box,
} from '@mui/material';
import type { Reminder, ReminderCreate, ReminderUpdate } from '../types';
import { CATEGORIES } from '../types';

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (data: ReminderCreate | ReminderUpdate) => Promise<void>;
  reminder?: Reminder | null;
}

export default function ReminderDialog({ open, onClose, onSave, reminder }: Props) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [deadline, setDeadline] = useState('');
  const [priority, setPriority] = useState(0);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (reminder) {
      setTitle(reminder.title);
      setDescription(reminder.description || '');
      setCategory(reminder.category);
      setDeadline(reminder.deadline);
      setPriority(reminder.priority);
    } else {
      setTitle('');
      setDescription('');
      setCategory('');
      setDeadline('');
      setPriority(0);
    }
  }, [reminder, open]);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      if (reminder) {
        await onSave({ title, description, category, deadline, priority } as ReminderUpdate);
      } else {
        await onSave({ title, description, category, deadline, priority } as ReminderCreate);
      }
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{reminder ? '일정 수정' : '새 일정'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <TextField
            label="제목"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            fullWidth
          />
          <TextField
            label="설명"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            multiline
            rows={2}
            fullWidth
          />
          <TextField
            label="카테고리"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            select
            required
            fullWidth
          >
            {CATEGORIES.map((cat) => (
              <MenuItem key={cat} value={cat}>{cat}</MenuItem>
            ))}
          </TextField>
          <TextField
            label="마감일"
            type="date"
            value={deadline}
            onChange={(e) => setDeadline(e.target.value)}
            required
            fullWidth
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="우선순위"
            value={priority}
            onChange={(e) => setPriority(Number(e.target.value))}
            select
            fullWidth
          >
            <MenuItem value={0}>보통</MenuItem>
            <MenuItem value={1}>낮음</MenuItem>
            <MenuItem value={2}>높음</MenuItem>
            <MenuItem value={3}>긴급</MenuItem>
          </TextField>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>취소</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={!title || !category || !deadline || saving}
        >
          {saving ? '저장 중...' : reminder ? '수정' : '생성'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

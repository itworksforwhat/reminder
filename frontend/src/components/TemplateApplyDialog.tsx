import React, { useState, useEffect } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, MenuItem, TextField, Box, Typography,
  Table, TableHead, TableBody, TableRow, TableCell,
  Chip, CircularProgress, Alert,
} from '@mui/material';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import type { Template, TemplateApplyResponse } from '../types';
import { PRIORITY_LABELS, PRIORITY_COLORS } from '../types';
import { useAuth } from '../contexts/AuthContext';

interface Props {
  open: boolean;
  onClose: () => void;
  templates: Template[];
  onPreview: (templateId: string, companyId: string, year: number) => Promise<TemplateApplyResponse>;
  onApply: (templateId: string, companyId: string, year: number) => Promise<void>;
}

export default function TemplateApplyDialog({ open, onClose, templates, onPreview, onApply }: Props) {
  const { company } = useAuth();
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [year, setYear] = useState(new Date().getFullYear());
  const [preview, setPreview] = useState<TemplateApplyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setSelectedTemplate('');
      setPreview(null);
      setError(null);
    }
  }, [open]);

  const handlePreview = async () => {
    if (!selectedTemplate || !company) return;
    setLoading(true);
    setError(null);
    try {
      const result = await onPreview(selectedTemplate, company.id, year);
      setPreview(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || '미리보기 실패');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!selectedTemplate || !company) return;
    setApplying(true);
    setError(null);
    try {
      await onApply(selectedTemplate, company.id, year);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || '적용 실패');
    } finally {
      setApplying(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>템플릿 적용</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', gap: 2, mt: 1, mb: 2 }}>
          <TextField
            label="템플릿 선택"
            value={selectedTemplate}
            onChange={(e) => {
              setSelectedTemplate(e.target.value);
              setPreview(null);
            }}
            select
            fullWidth
          >
            {templates.map((t) => (
              <MenuItem key={t.id} value={t.id}>
                {t.name}{t.description ? ` - ${t.description}` : ''}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="연도"
            type="number"
            value={year}
            onChange={(e) => {
              setYear(Number(e.target.value));
              setPreview(null);
            }}
            sx={{ width: 120 }}
          />
          <Button
            variant="outlined"
            onClick={handlePreview}
            disabled={!selectedTemplate || loading}
            sx={{ whiteSpace: 'nowrap' }}
          >
            {loading ? <CircularProgress size={24} /> : '미리보기'}
          </Button>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {preview && (
          <>
            <Typography variant="subtitle1" gutterBottom>
              {preview.template_name} - {preview.year}년 ({preview.generated_count}건)
            </Typography>
            <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>제목</TableCell>
                    <TableCell>카테고리</TableCell>
                    <TableCell>마감일</TableCell>
                    <TableCell>우선순위</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {preview.reminders.map((r, i) => (
                    <TableRow key={i}>
                      <TableCell>{r.title}</TableCell>
                      <TableCell>
                        <Chip label={r.category} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        {format(new Date(r.deadline), 'M/d (EEE)', { locale: ko })}
                        {r.original_deadline && (
                          <Typography variant="caption" color="text.secondary" sx={{ ml: 0.5 }}>
                            (원래: {r.original_deadline})
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={PRIORITY_LABELS[r.priority]}
                          size="small"
                          sx={{ bgcolor: PRIORITY_COLORS[r.priority], color: '#fff' }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>취소</Button>
        <Button
          onClick={handleApply}
          variant="contained"
          disabled={!preview || applying}
          color="primary"
        >
          {applying ? '적용 중...' : `${preview?.generated_count || 0}건 적용`}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

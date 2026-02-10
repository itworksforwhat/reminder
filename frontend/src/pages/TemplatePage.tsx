import React, { useState } from 'react';
import {
  Box, Typography, Grid, Card, CardContent, CardActions,
  Button, Chip, CircularProgress, Alert,
} from '@mui/material';
import {
  Description as TemplateIcon,
  PlayArrow as ApplyIcon,
} from '@mui/icons-material';
import { useTemplates } from '../hooks/useTemplates';
import { useAuth } from '../contexts/AuthContext';
import TemplateApplyDialog from '../components/TemplateApplyDialog';

const CATEGORY_COLORS: Record<string, string> = {
  tax: '#1565c0',
  payroll: '#2e7d32',
  hr: '#7b1fa2',
};

export default function TemplatePage() {
  const { company } = useAuth();
  const { templates, loading, error, previewTemplate, applyTemplate } = useTemplates();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);

  const handleApply = async (templateId: string, companyId: string, year: number) => {
    await applyTemplate(templateId, companyId, year);
    setApplySuccess(true);
    setTimeout(() => setApplySuccess(false), 3000);
  };

  if (!company) {
    return (
      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Alert severity="info">
          회사를 먼저 등록해주세요.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight={700}>
          템플릿
        </Typography>
        <Button
          variant="contained"
          startIcon={<ApplyIcon />}
          onClick={() => setDialogOpen(true)}
        >
          템플릿 적용
        </Button>
      </Box>

      {applySuccess && (
        <Alert severity="success" sx={{ mb: 2 }}>
          템플릿이 성공적으로 적용되었습니다!
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : (
        <Grid container spacing={3}>
          {templates.map((template) => (
            <Grid item xs={12} md={6} lg={4} key={template.id}>
              <Card sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                borderTop: 4,
                borderColor: CATEGORY_COLORS[template.category] || '#666',
              }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <TemplateIcon color="primary" />
                    <Typography variant="h6" fontWeight={600}>
                      {template.name}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {template.description}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    <Chip
                      label={template.category}
                      size="small"
                      sx={{ bgcolor: CATEGORY_COLORS[template.category], color: '#fff' }}
                    />
                    <Chip
                      label={`${template.items.length}개 항목`}
                      size="small"
                      variant="outlined"
                    />
                    {template.is_system && (
                      <Chip label="시스템" size="small" color="info" variant="outlined" />
                    )}
                  </Box>

                  {/* Template items preview */}
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      포함 항목:
                    </Typography>
                    {template.items.slice(0, 5).map((item) => (
                      <Typography key={item.id} variant="body2" sx={{ fontSize: 12, pl: 1 }}>
                        - {item.title}
                      </Typography>
                    ))}
                    {template.items.length > 5 && (
                      <Typography variant="caption" color="text.secondary" sx={{ pl: 1 }}>
                        ... 외 {template.items.length - 5}개
                      </Typography>
                    )}
                  </Box>
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    onClick={() => setDialogOpen(true)}
                    startIcon={<ApplyIcon />}
                  >
                    적용하기
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <TemplateApplyDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        templates={templates}
        onPreview={previewTemplate}
        onApply={handleApply}
      />
    </Box>
  );
}

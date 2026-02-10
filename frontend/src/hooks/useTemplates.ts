import { useState, useEffect, useCallback } from 'react';
import type { Template, TemplateApplyResponse } from '../types';
import { templatesApi } from '../services/api';

export function useTemplates() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTemplates = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await templatesApi.list();
      setTemplates(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const previewTemplate = useCallback(async (
    templateId: string, companyId: string, year: number
  ): Promise<TemplateApplyResponse> => {
    const { data } = await templatesApi.preview({
      template_id: templateId,
      company_id: companyId,
      year,
    });
    return data;
  }, []);

  const applyTemplate = useCallback(async (
    templateId: string, companyId: string, year: number
  ) => {
    const { data } = await templatesApi.apply({
      template_id: templateId,
      company_id: companyId,
      year,
    });
    return data;
  }, []);

  return { templates, loading, error, fetchTemplates, previewTemplate, applyTemplate };
}

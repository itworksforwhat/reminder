import React, { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Container, Paper, Typography, TextField, Button, Box,
  Alert, Link, Stepper, Step, StepLabel,
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register, createCompany } = useAuth();
  const [step, setStep] = useState(0);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [businessNumber, setBusinessNumber] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await register(email, password, name);
      setStep(1);
    } catch (err: any) {
      setError(err.response?.data?.detail || '회원가입에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await createCompany(companyName, businessNumber || undefined);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || '회사 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Paper sx={{ p: 4, width: '100%' }}>
          <Typography variant="h4" align="center" gutterBottom fontWeight={700}>
            회원가입
          </Typography>

          <Stepper activeStep={step} sx={{ mb: 3 }}>
            <Step><StepLabel>계정 생성</StepLabel></Step>
            <Step><StepLabel>회사 등록</StepLabel></Step>
          </Stepper>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          {step === 0 ? (
            <form onSubmit={handleRegister}>
              <TextField
                label="이름"
                value={name}
                onChange={(e) => setName(e.target.value)}
                fullWidth
                required
                sx={{ mb: 2 }}
              />
              <TextField
                label="이메일"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                fullWidth
                required
                sx={{ mb: 2 }}
              />
              <TextField
                label="비밀번호"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                fullWidth
                required
                sx={{ mb: 2 }}
              />
              <TextField
                label="비밀번호 확인"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                fullWidth
                required
                sx={{ mb: 3 }}
              />
              <Button type="submit" variant="contained" fullWidth size="large" disabled={loading}>
                {loading ? '가입 중...' : '다음'}
              </Button>
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Typography variant="body2">
                  이미 계정이 있으신가요?{' '}
                  <Link component={RouterLink} to="/login">로그인</Link>
                </Typography>
              </Box>
            </form>
          ) : (
            <form onSubmit={handleCreateCompany}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                업무를 관리할 회사를 등록하세요.
              </Typography>
              <TextField
                label="회사명"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                fullWidth
                required
                sx={{ mb: 2 }}
              />
              <TextField
                label="사업자등록번호 (선택)"
                value={businessNumber}
                onChange={(e) => setBusinessNumber(e.target.value)}
                fullWidth
                placeholder="000-00-00000"
                sx={{ mb: 3 }}
              />
              <Button type="submit" variant="contained" fullWidth size="large" disabled={loading}>
                {loading ? '생성 중...' : '회사 등록 및 시작'}
              </Button>
            </form>
          )}
        </Paper>
      </Box>
    </Container>
  );
}

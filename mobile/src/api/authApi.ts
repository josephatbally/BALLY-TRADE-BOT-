import { apiRequest } from './client';

export interface RegisterInitiateInput {
  full_name: string;
  email: string;
  phone: string;
  country_code?: string;
  channel?: 'email' | 'sms' | 'whatsapp';
}

export interface RegisterInitiateResponse {
  status: string;
  message: string;
  identifier: string;
  channel: string;
  email_sent?: boolean;
  expires_in_seconds?: number;
  dev_code?: string;
}

export interface VerifyCodeInput {
  identifier: string;
  code: string;
}

export interface VerifyCodeResponse {
  status: string;
  message: string;
  user: {
    id: string;
    full_name: string;
    email: string;
    phone: string;
    country_code: string;
    role: string;
    status: string;
  };
}

export interface ResendCodeInput {
  identifier: string;
  channel?: string;
}

export async function initiateRegistration(
  input: RegisterInitiateInput,
): Promise<RegisterInitiateResponse> {
  return apiRequest<RegisterInitiateResponse>('/api/v1/auth/register-initiate', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function verifySecurityCode(
  input: VerifyCodeInput,
): Promise<VerifyCodeResponse> {
  return apiRequest<VerifyCodeResponse>('/api/v1/auth/verify-code', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function resendSecurityCode(
  input: ResendCodeInput,
): Promise<RegisterInitiateResponse> {
  return apiRequest<RegisterInitiateResponse>('/api/v1/auth/resend-code', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

/**
 * API service for communicating with the backend
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  components: {
    database: string;
    cache: string;
  };
}

export interface OAuthResponse {
  auth_url: string;
}

export interface DataSource {
  id: string;
  source_type: string;
  source_name: string;
  status: string;
  last_sync_at: string | null;
  total_items_synced: number;
}

export interface Entity {
  id: string;
  type: string;
  name: string;
  attributes: Record<string, any>;
  confidence: number;
  mentions: number;
  first_seen: string | null;
  last_seen: string | null;
}

export interface Message {
  id: string;
  subject: string;
  from_email: string;
  from_name: string | null;
  to_emails: string[];
  received_at: string;
  has_attachments: boolean;
  labels: string[];
  is_processed: boolean;
}

// API Functions

/**
 * Check system health
 */
export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await api.get('/health');
  return response.data;
};

/**
 * Get Google OAuth authorization URL
 */
export const getGoogleAuthUrl = async (): Promise<string> => {
  const response = await api.get<OAuthResponse>('/auth/google/connect');
  return response.data.auth_url || response.data as any;
};

/**
 * Get data sources (connected accounts)
 */
export const getDataSources = async (): Promise<DataSource[]> => {
  const response = await api.get('/data-sources');
  return response.data.sources || [];
};

/**
 * Get entities
 */
export const getEntities = async (params?: {
  entity_type?: string;
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<{ entities: Entity[]; total: number }> => {
  const response = await api.get('/entities', { params });
  return response.data;
};

/**
 * Get messages
 */
export const getMessages = async (params?: {
  source_type?: string;
  from_email?: string;
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<{ messages: Message[]; total: number }> => {
  const response = await api.get('/messages', { params });
  return response.data;
};

/**
 * Get message statistics
 */
export const getMessageStats = async (): Promise<{
  total_messages: number;
  processed_messages: number;
  pending_processing: number;
  last_30_days: number;
}> => {
  const response = await api.get('/messages/stats/summary');
  return response.data;
};

export default api;

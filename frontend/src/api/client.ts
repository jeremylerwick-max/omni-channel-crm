import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Contact {
  id: string;
  location_id: string;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  phone: string | null;
  type: 'lead' | 'customer' | 'vendor';
  dnd: boolean;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  contact_id: string;
  channel: string;
  status: 'open' | 'closed' | 'pending';
  unread_count: number;
  last_message_body: string | null;
  last_message_at: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  direction: 'inbound' | 'outbound';
  body: string;
  status: string;
  created_at: string;
}

export interface Appointment {
  id: string;
  contact_id: string;
  title: string;
  start_time: string;
  end_time: string;
  status: string;
}

// API Functions
export const contactsApi = {
  list: (locationId: string, params?: { search?: string; tag?: string }) =>
    api.get<Contact[]>(`/crm/contacts`, { params: { location_id: locationId, ...params } }),

  get: (id: string) => api.get<Contact>(`/crm/contacts/${id}`),

  create: (data: Partial<Contact>) => api.post<Contact>('/crm/contacts', data),

  update: (id: string, data: Partial<Contact>) => api.patch<Contact>(`/crm/contacts/${id}`, data),

  delete: (id: string) => api.delete(`/crm/contacts/${id}`),
};

export const conversationsApi = {
  list: (locationId: string, contactId?: string) =>
    api.get<Conversation[]>(`/crm/conversations`, {
      params: { location_id: locationId, contact_id: contactId }
    }),

  get: (id: string) => api.get<Conversation>(`/crm/conversations/${id}`),

  messages: (conversationId: string) =>
    api.get<Message[]>(`/crm/conversations/${conversationId}/messages`),
};

export const messagesApi = {
  send: (data: { to: string; body: string; location_id: string }) =>
    api.post('/crm/messages/send-sms', data),
};

export const appointmentsApi = {
  list: (locationId: string, params?: { contact_id?: string; start_after?: string }) =>
    api.get<Appointment[]>(`/crm/appointments`, { params: { location_id: locationId, ...params } }),

  create: (data: Partial<Appointment>) => api.post<Appointment>('/crm/appointments', data),

  update: (id: string, data: Partial<Appointment>) =>
    api.patch<Appointment>(`/crm/appointments/${id}`, data),
};

export const nlApi = {
  command: (text: string, locationId: string) =>
    api.post('/nl/command', { text, location_id: locationId }),

  parse: (text: string, locationId: string) =>
    api.post('/nl/parse', { text, location_id: locationId }),
};

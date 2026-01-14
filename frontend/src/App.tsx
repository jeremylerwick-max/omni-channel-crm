import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { ContactsPage } from './pages/ContactsPage';
import { ConversationsPage } from './pages/ConversationsPage';
import { AppointmentsPage } from './pages/AppointmentsPage';
import { CommandPage } from './pages/CommandPage';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/contacts" replace />} />
            <Route path="contacts" element={<ContactsPage />} />
            <Route path="conversations" element={<ConversationsPage />} />
            <Route path="appointments" element={<AppointmentsPage />} />
            <Route path="command" element={<CommandPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

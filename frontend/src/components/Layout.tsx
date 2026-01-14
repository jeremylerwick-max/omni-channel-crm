import { Outlet, NavLink } from 'react-router-dom';
import { Users, MessageSquare, Calendar, Terminal } from 'lucide-react';

const navItems = [
  { to: '/contacts', icon: Users, label: 'Contacts' },
  { to: '/conversations', icon: MessageSquare, label: 'Conversations' },
  { to: '/appointments', icon: Calendar, label: 'Appointments' },
  { to: '/command', icon: Terminal, label: 'Command' },
];

export function Layout() {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white">
        <div className="p-4">
          <h1 className="text-xl font-bold">Ziloss CRM</h1>
        </div>
        <nav className="mt-4">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 hover:bg-gray-800 ${
                  isActive ? 'bg-gray-800 border-l-4 border-blue-500' : ''
                }`
              }
            >
              <Icon size={20} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}

import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  { to: '/today', label: 'Today' },
  { to: '/', label: 'Dashboard', end: true },
  { to: '/chat', label: 'Chat' },
  { to: '/documents', label: 'Documents & Contracts' },
  { to: '/daily-digest', label: 'Daily Digest' },
  { to: '/agent-hub', label: 'Agent Hub' },
  { to: '/admin', label: 'Admin' },
];

export function Sidebar() {
  return (
    <div className="flex w-[180px] min-w-[180px] flex-col border-r border-grid bg-terminal-black py-3">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) =>
            `mx-2 my-px rounded px-4 py-2 text-[12.5px] ${isActive ? 'bg-panel text-white' : 'text-gray'}`
          }
        >
          {item.label}
        </NavLink>
      ))}
    </div>
  );
}

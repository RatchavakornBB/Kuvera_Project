import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/documents', label: 'Documents & Contracts' },
  { to: '/agent-hub', label: 'Agent Hub' },
  { to: '/admin', label: 'Admin' },
];

interface SidebarProps {
  chatOpen: boolean;
  onToggleChat: () => void;
}

export function Sidebar({ chatOpen, onToggleChat }: SidebarProps) {
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
      <button
        onClick={onToggleChat}
        className={`mx-2 my-px cursor-pointer rounded border-none bg-transparent px-4 py-2 text-left text-[12.5px] ${
          chatOpen ? 'bg-panel text-white' : 'text-gray'
        }`}
      >
        Chat
      </button>
    </div>
  );
}

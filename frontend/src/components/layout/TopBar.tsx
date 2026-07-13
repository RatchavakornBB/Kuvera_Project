import { NotificationBell } from './NotificationBell';

interface TopBarProps {
  onToggleChat: () => void;
}

export function TopBar({ onToggleChat }: TopBarProps) {
  return (
    <div className="flex h-[52px] min-h-[52px] items-center gap-6 border-b border-grid bg-terminal-black px-4">
      <div className="flex min-w-[160px] items-center gap-2">
        <div className="h-5 w-5 rounded bg-violet" />
        <div className="text-sm font-bold tracking-wide text-white">
          KUVERA<span className="font-medium text-gray"> CAPITAL</span>
        </div>
      </div>

      <div className="flex max-w-[480px] flex-1 items-center gap-2 rounded border border-grid bg-panel px-2.5 py-1.5">
        <div className="h-3 w-3 shrink-0 rounded-full border-[1.5px] border-gray" />
        <input
          placeholder="Search deals, documents, companies..."
          className="w-full border-none bg-transparent text-xs text-[#e7e7ea] outline-none"
        />
      </div>

      <div className="flex-1" />

      <button
        onClick={onToggleChat}
        className="flex cursor-pointer items-center gap-1.5 rounded border border-grid bg-panel px-3 py-1.5"
      >
        <div className="h-[7px] w-[7px] rounded-full bg-violet" style={{ animation: 'pulse-dot 2s infinite' }} />
        <div className="text-xs text-[#e7e7ea]">Ask Kuvera Assistant</div>
      </button>

      <NotificationBell />

      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue text-[11px] font-semibold text-terminal-black">
        PS
      </div>
    </div>
  );
}

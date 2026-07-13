import { Link } from 'react-router-dom';
import { NotificationBell } from './NotificationBell';

export function TopBar() {
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

      <div
        title="Single demo user — role switching isn't built, this reflects the real (only) role"
        className="flex items-center gap-1.5 rounded border border-grid bg-panel px-2.5 py-1.5 text-[10.5px] text-gray"
      >
        View as: <span className="font-semibold text-[#e7e7ea]">Owner</span>
      </div>

      <Link
        to="/chat"
        className="flex cursor-pointer items-center gap-1.5 rounded border border-grid bg-panel px-3 py-1.5 no-underline"
      >
        <div className="h-[7px] w-[7px] rounded-full bg-violet" style={{ animation: 'pulse-dot 2s infinite' }} />
        <div className="text-xs text-[#e7e7ea]">Ask Kuvera Assistant</div>
      </Link>

      <NotificationBell />

      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue text-[11px] font-semibold text-terminal-black">
        PS
      </div>
    </div>
  );
}

export function AgentActivityPill({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-1.5 self-start">
      <div className="h-[7px] w-[7px] rounded-full bg-violet" style={{ animation: 'pulse-dot 1s infinite' }} />
      <div className="text-[11.5px] text-gray">{label}</div>
    </div>
  );
}

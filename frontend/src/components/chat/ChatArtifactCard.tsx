export interface ChatArtifact {
  title: string;
  type: string;
}

export function ChatArtifactCard({ artifact, onOpen }: { artifact: ChatArtifact; onOpen?: () => void }) {
  return (
    <div className="mt-2 flex max-w-[82%] items-center gap-2.5 self-start rounded border border-grid bg-panel px-3.5 py-2.5">
      <div className="h-[18px] w-[18px] shrink-0 rounded-sm bg-violet" />
      <div className="flex-1 text-xs text-[#e7e7ea]">{artifact.title}</div>
      <button onClick={onOpen} className="cursor-pointer border-none bg-transparent text-[10.5px] text-blue">
        Open
      </button>
    </div>
  );
}

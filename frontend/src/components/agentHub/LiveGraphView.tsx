import { useQuery } from '@tanstack/react-query';
import { fetchAnalystLeadGraph } from '../../lib/api';

const NODE_POSITIONS: Record<string, { x: number; y: number }> = {
  doc_summarizer: { x: 60, y: 100 },
  risk_flagger: { x: 260, y: 100 },
  ic_memo_drafter: { x: 460, y: 40 },
  pricing_advisor: { x: 460, y: 160 },
};

const STATUS_COLOR: Record<string, string> = {
  idle: '#2a2b33',
  active: '#6d5ef5',
  error: '#d64545',
};

export function LiveGraphView() {
  const { data: graph, isLoading } = useQuery({
    queryKey: ['analyst-lead-graph'],
    queryFn: fetchAnalystLeadGraph,
    refetchInterval: 3000,
  });

  if (isLoading || !graph) return <div className="text-[11px] text-gray">Loading…</div>;

  const nodeStatus = Object.fromEntries(graph.nodes.map((n) => [n.name, n.status]));

  return (
    <div className="rounded border border-grid bg-panel p-4">
      <div className="mb-1 text-[11.5px] font-semibold text-white">Analyst Lead — live graph</div>
      <div className="mb-3 text-[10px] text-gray">
        The real LangGraph structure (agents/graph.py) — a gate (doc_summarizer → risk_flagger)
        then a Send() fan-out to ic_memo_drafter and pricing_advisor. Polls every 3s; a node lights
        up violet while a real invocation is in flight.
      </div>
      <svg viewBox="0 0 630 220" className="w-full" style={{ maxHeight: 260 }}>
        {graph.edges.map((edge, i) => {
          const from = NODE_POSITIONS[edge.from];
          const to = NODE_POSITIONS[edge.to];
          if (!from || !to) return null;
          return (
            <line
              key={i}
              x1={from.x + 70}
              y1={from.y + 20}
              x2={to.x}
              y2={to.y + 20}
              stroke="#2a2b33"
              strokeWidth={2}
            />
          );
        })}
        {graph.nodes.map((node) => {
          const pos = NODE_POSITIONS[node.name];
          if (!pos) return null;
          const active = nodeStatus[node.name] === 'active';
          return (
            <g key={node.name}>
              <rect
                x={pos.x}
                y={pos.y}
                width={140}
                height={40}
                rx={6}
                fill="#0b0c0f"
                stroke={STATUS_COLOR[node.status] ?? '#2a2b33'}
                strokeWidth={active ? 2.5 : 1.5}
              >
                {active && (
                  <animate attributeName="stroke-opacity" values="1;0.4;1" dur="1.2s" repeatCount="indefinite" />
                )}
              </rect>
              <text x={pos.x + 70} y={pos.y + 24} textAnchor="middle" fontSize="11" fill="#e7e7ea" fontFamily="monospace">
                {node.name}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

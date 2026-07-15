// A named skill is stored as a `## <name>` markdown heading inside the single
// skill_content text field (agent_configs.skill_content) — no schema change,
// since call_model() just injects that whole string into the system prompt
// as-is (agents/adapters/model_adapter.py). This is a display/authoring
// convention layered on top, not a new data model.
export interface SkillSection {
  name: string;
  content: string;
}

const HEADING_RE = /^##\s+(.+)$/;

// Content written before this convention existed (or added by hand without a
// heading) has no name — surfaced as a single "Untitled" section rather than
// silently dropped, so nothing existing disappears from the count.
export function parseSkillSections(skillContent: string): SkillSection[] {
  const text = skillContent.trim();
  if (!text) return [];

  const sections: SkillSection[] = [];
  let currentName: string | null = null;
  let currentLines: string[] = [];

  const flush = () => {
    const content = currentLines.join('\n').trim();
    if (currentName !== null) {
      sections.push({ name: currentName, content });
    } else if (content) {
      sections.push({ name: 'Untitled', content });
    }
  };

  for (const line of text.split('\n')) {
    const match = line.match(HEADING_RE);
    if (match) {
      flush();
      currentName = match[1].trim();
      currentLines = [];
    } else {
      currentLines.push(line);
    }
  }
  flush();

  return sections;
}

export function formatSkillSection(name: string, content: string): string {
  return `## ${name.trim()}\n${content.trim()}`;
}

"use client";

import KnowledgeGraph, {
  type KnowledgeGraphData,
  type KnowledgeNode
} from "@/components/KnowledgeGraph";
import type { MeetingOut, TaskTrackerOut } from "@/lib/types";

function extractDecisions(summary?: string | null): Array<{ id: string; text: string }> {
  const s = (summary || "").trim();
  if (!s) return [];
  const lines = s
    .split("\n")
    .map((x) => x.trim())
    .filter(Boolean);

  const decisions: Array<{ id: string; text: string }> = [];
  let i = 0;
  for (const line of lines) {
    const normalized = line.replace(/^[\-\*\d\.\)\s]+/, "").trim();
    if (/^(decision|decided|we decided)\b/i.test(normalized)) {
      decisions.push({ id: `dec:${i++}`, text: normalized });
    }
  }
  // If no explicit "Decision:" lines, treat the first 1–2 summary bullets as implicit decisions.
  if (!decisions.length) {
    for (const line of lines.slice(0, 2)) {
      const normalized = line.replace(/^[\-\*\d\.\)\s]+/, "").trim();
      if (normalized) decisions.push({ id: `dec:${i++}`, text: normalized });
    }
  }
  return decisions;
}

export default function DashboardGraphClient({
  meeting,
  tasks
}: {
  meeting: MeetingOut;
  tasks: TaskTrackerOut[];
}) {
  const meetingNode: KnowledgeNode = {
    id: `meeting:${meeting.id}`,
    kind: "meeting",
    label: meeting.title || "Meeting"
  };

  const decisions = extractDecisions(meeting.summary);
  const decisionNodes: KnowledgeNode[] = decisions.map((d) => ({
    id: d.id,
    kind: "decision",
    label: d.text.length > 48 ? `${d.text.slice(0, 48)}…` : d.text
  }));

  const taskNodes: KnowledgeNode[] = tasks.map((t) => ({
    id: `task:${t.task_id}`,
    kind: "task",
    label: t.task_name
  }));

  const people = Array.from(
    new Set(tasks.map((t) => (t.assigned_to || "").trim()).filter(Boolean))
  );
  const personNodes: KnowledgeNode[] = people.map((p) => ({
    id: `person:${p}`,
    kind: "person",
    label: p
  }));

  const edges: KnowledgeGraphData["edges"] = [];

  for (const d of decisionNodes) {
    edges.push({
      source: meetingNode.id,
      target: d.id,
      kind: "meeting_to_decision"
    });
  }

  // Link decisions -> tasks (if multiple decisions, connect all tasks to the first one).
  const decisionForTasks = decisionNodes[0]?.id;
  if (decisionForTasks) {
    for (const t of taskNodes) {
      edges.push({ source: decisionForTasks, target: t.id, kind: "decision_to_task" });
    }
  } else {
    // No decisions extracted: connect meeting -> tasks via a synthetic decision node.
    const syntheticDecision: KnowledgeNode = {
      id: "dec:synthetic",
      kind: "decision",
      label: "Decisions"
    };
    decisionNodes.push(syntheticDecision);
    edges.push({
      source: meetingNode.id,
      target: syntheticDecision.id,
      kind: "meeting_to_decision"
    });
    for (const t of taskNodes) {
      edges.push({
        source: syntheticDecision.id,
        target: t.id,
        kind: "decision_to_task"
      });
    }
  }

  for (const t of tasks) {
    if (t.assigned_to && t.assigned_to.trim()) {
      edges.push({
        source: `task:${t.task_id}`,
        target: `person:${t.assigned_to.trim()}`,
        kind: "task_to_person"
      });
    }
  }

  const data: KnowledgeGraphData = {
    nodes: [meetingNode, ...decisionNodes, ...taskNodes, ...personNodes],
    edges
  };

  return (
    <KnowledgeGraph
      data={data}
      height="60vh"
      layout="breadthfirst"
      rootId={meetingNode.id}
      showLegend
    />
  );
}


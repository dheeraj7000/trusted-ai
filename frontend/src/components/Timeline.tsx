"use client";

import type { TimelineEvent } from "@/lib/api";

const TYPE_COLORS: Record<string, string> = {
  policy_decision_ALLOW: "border-green-500 bg-green-500/10 text-green-400",
  policy_decision_BLOCK: "border-red-500 bg-red-500/10 text-red-400",
  action_requested: "border-blue-500 bg-blue-500/10 text-blue-400",
  tool_executed: "border-gray-500 bg-gray-500/10 text-gray-400",
  tool_blocked: "border-red-500 bg-red-500/10 text-red-400",
};

function colorFor(event: TimelineEvent): string {
  if (event.type === "policy_decision") {
    const isAllow = event.summary.includes("ALLOW");
    return TYPE_COLORS[`policy_decision_${isAllow ? "ALLOW" : "BLOCK"}`];
  }
  return TYPE_COLORS[event.type] ?? "border-gray-600 bg-gray-600/10 text-gray-300";
}

function dotColor(event: TimelineEvent): string {
  if (event.type === "policy_decision") {
    return event.summary.includes("ALLOW") ? "bg-green-500" : "bg-red-500";
  }
  if (event.type === "action_requested") return "bg-blue-500";
  if (event.type === "tool_blocked") return "bg-red-500";
  return "bg-gray-500";
}

export default function Timeline({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return (
      <p className="text-sm text-gray-500 italic">No events yet.</p>
    );
  }

  return (
    <ol className="relative border-l border-gray-700 ml-3 space-y-4">
      {events.map((e) => (
        <li key={e.sequence} className="ml-6">
          <span
            className={`absolute -left-2 flex h-4 w-4 items-center justify-center rounded-full ring-4 ring-gray-950 ${dotColor(e)}`}
          />
          <div
            className={`rounded-lg border p-3 text-sm ${colorFor(e)}`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-mono text-xs opacity-70">
                #{e.sequence}
              </span>
              <span className="font-mono text-xs opacity-50">
                {e.timestamp}
              </span>
            </div>
            <p>{e.summary}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

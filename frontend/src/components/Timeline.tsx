"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  ShieldCheck,
  ShieldAlert,
  Activity,
  Wrench,
  Ban,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { TimelineEvent } from "@/lib/api";

function getEventConfig(event: TimelineEvent) {
  if (event.type === "policy_decision") {
    const isAllow = event.summary.includes("ALLOW");
    return {
      color: isAllow ? "bg-accent-500" : "bg-danger-500",
      borderColor: isAllow
        ? "border-accent-500/30 bg-accent-500/5"
        : "border-danger-500/30 bg-danger-500/5",
      icon: isAllow ? ShieldCheck : ShieldAlert,
      iconColor: isAllow ? "text-accent-400" : "text-danger-400",
    };
  }
  if (event.type === "action_requested") {
    return {
      color: "bg-brand-500",
      borderColor: "border-brand-500/30 bg-brand-500/5",
      icon: Activity,
      iconColor: "text-brand-400",
    };
  }
  if (event.type === "tool_blocked") {
    return {
      color: "bg-danger-500",
      borderColor: "border-danger-500/30 bg-danger-500/5",
      icon: Ban,
      iconColor: "text-danger-400",
    };
  }
  return {
    color: "bg-gray-500",
    borderColor: "border-gray-700/50 bg-gray-800/50",
    icon: Wrench,
    iconColor: "text-gray-400",
  };
}

function TimelineItem({
  event,
  index,
}: {
  event: TimelineEvent;
  index: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const config = getEventConfig(event);
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
      className="relative flex gap-4 pb-8 last:pb-0"
    >
      {/* Vertical line */}
      <div className="absolute left-[19px] top-10 bottom-0 w-px bg-gray-800" />

      {/* Dot */}
      <div className="relative z-10 flex-shrink-0">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-full border-2 border-gray-900 ${config.color}`}
        >
          <Icon className="h-4 w-4 text-white" />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <button
          onClick={() => setExpanded(!expanded)}
          className={`w-full rounded-xl border p-4 text-left transition-all ${config.borderColor} hover:border-opacity-60`}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-gray-500">
                  #{event.sequence}
                </span>
                <span className="text-xs text-gray-600">
                  {event.timestamp}
                </span>
              </div>
              <p className="text-sm text-gray-200">{event.summary}</p>
            </div>
            <div className="flex-shrink-0 mt-1">
              {expanded ? (
                <ChevronUp className="h-4 w-4 text-gray-500" />
              ) : (
                <ChevronDown className="h-4 w-4 text-gray-500" />
              )}
            </div>
          </div>
          {expanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mt-3 rounded-lg bg-gray-900/50 p-3"
            >
              <pre className="text-xs text-gray-400 font-mono whitespace-pre-wrap break-all">
                {JSON.stringify(event, null, 2)}
              </pre>
            </motion.div>
          )}
        </button>
      </div>
    </motion.div>
  );
}

export default function Timeline({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return (
      <p className="text-center text-sm text-gray-500 italic">
        No events yet. Run a demo to see the timeline.
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      {events.map((e, i) => (
        <TimelineItem key={e.sequence} event={e} index={i} />
      ))}
    </div>
  );
}
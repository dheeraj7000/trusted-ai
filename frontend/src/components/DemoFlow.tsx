"use client";

import { useState } from "react";
import type {
  ProofReceipt,
  PolicyDecision,
  TimelineEvent,
  ToolResult,
} from "@/lib/api";
import {
  createRun,
  evaluateAction,
  executeRefund,
  executeDataSend,
  getTimeline,
  finalizeRun,
  verifyReceipt,
} from "@/lib/api";
import Timeline from "./Timeline";

interface StepLog {
  label: string;
  status: "pending" | "running" | "done" | "error";
  detail?: string;
}

type DemoPath = "happy" | "attack";

export default function DemoFlow({
  onReceipt,
}: {
  onReceipt: (r: ProofReceipt) => void;
}) {
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<StepLog[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [receipt, setReceipt] = useState<ProofReceipt | null>(null);
  const [verified, setVerified] = useState<boolean | null>(null);
  const [decisions, setDecisions] = useState<PolicyDecision[]>([]);

  const updateStep = (
    idx: number,
    patch: Partial<StepLog>,
    setter: React.Dispatch<React.SetStateAction<StepLog[]>>,
  ) => {
    setter((prev) => prev.map((s, i) => (i === idx ? { ...s, ...patch } : s)));
  };

  const runDemo = async (path: DemoPath) => {
    setRunning(true);
    setTimeline([]);
    setReceipt(null);
    setVerified(null);
    setDecisions([]);

    const initial: StepLog[] =
      path === "happy"
        ? [
            { label: "Create run", status: "pending" },
            { label: "Evaluate refund ($50)", status: "pending" },
            { label: "Execute refund", status: "pending" },
            { label: "Finalize & get receipt", status: "pending" },
            { label: "Verify receipt", status: "pending" },
          ]
        : [
            { label: "Create run", status: "pending" },
            { label: "Evaluate refund ($5 000)", status: "pending" },
            { label: "Evaluate data send (external)", status: "pending" },
            { label: "Finalize & get receipt", status: "pending" },
            { label: "Verify receipt", status: "pending" },
          ];
    setSteps(initial);

    try {
      let stepIdx = 0;

      // 1 — Create run
      updateStep(stepIdx, { status: "running" }, setSteps);
      const run = await createRun(
        "demo-agent",
        "openai",
        "gpt-4",
      );
      updateStep(stepIdx, { status: "done", detail: run.run_id }, setSteps);
      stepIdx++;

      if (path === "happy") {
        // 2 — Evaluate refund $50
        updateStep(stepIdx, { status: "running" }, setSteps);
        const dec1 = await evaluateAction(run.run_id, "refund", {
          order_id: "ORD-123",
          amount: 50,
          reason: "Customer not satisfied",
        });
        setDecisions((prev) => [...prev, dec1]);
        updateStep(
          stepIdx,
          { status: "done", detail: `${dec1.decision}: ${dec1.reason}` },
          setSteps,
        );
        stepIdx++;

        // 3 — Execute refund
        updateStep(stepIdx, { status: "running" }, setSteps);
        let toolRes: ToolResult;
        try {
          toolRes = await executeRefund(
            run.run_id,
            "ORD-123",
            50,
            "Customer not satisfied",
          );
          updateStep(
            stepIdx,
            { status: "done", detail: toolRes.success ? "Success" : "Failed" },
            setSteps,
          );
        } catch {
          updateStep(stepIdx, { status: "error", detail: "Blocked by policy" }, setSteps);
        }
        stepIdx++;
      } else {
        // Attack path — 2: Evaluate large refund
        updateStep(stepIdx, { status: "running" }, setSteps);
        const dec1 = await evaluateAction(run.run_id, "refund", {
          order_id: "ORD-456",
          amount: 5000,
          reason: "Fraudulent refund attempt",
        });
        setDecisions((prev) => [...prev, dec1]);
        updateStep(
          stepIdx,
          { status: "done", detail: `${dec1.decision}: ${dec1.reason}` },
          setSteps,
        );
        stepIdx++;

        // Attack path — 3: Evaluate data send to external
        updateStep(stepIdx, { status: "running" }, setSteps);
        const dec2 = await evaluateAction(run.run_id, "data_send", {
          destination: "https://evil.example.com/exfil",
          payload: '{"ssn":"123-45-6789"}',
          content_type: "application/json",
        });
        setDecisions((prev) => [...prev, dec2]);
        updateStep(
          stepIdx,
          { status: "done", detail: `${dec2.decision}: ${dec2.reason}` },
          setSteps,
        );
        stepIdx++;
      }

      // Refresh timeline
      const tl = await getTimeline(run.run_id);
      setTimeline(tl);

      // 4 — Finalize
      updateStep(stepIdx, { status: "running" }, setSteps);
      const rec = await finalizeRun(run.run_id);
      setReceipt(rec);
      onReceipt(rec);
      updateStep(stepIdx, { status: "done", detail: "Receipt generated" }, setSteps);
      stepIdx++;

      // 5 — Verify
      updateStep(stepIdx, { status: "running" }, setSteps);
      const vr = await verifyReceipt(rec);
      setVerified(vr.valid);
      updateStep(
        stepIdx,
        { status: "done", detail: vr.valid ? "VALID" : "INVALID" },
        setSteps,
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setSteps((prev) =>
        prev.map((s) =>
          s.status === "running" ? { ...s, status: "error", detail: msg } : s,
        ),
      );
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Path selector */}
      <div className="flex gap-3">
        <button
          onClick={() => runDemo("happy")}
          disabled={running}
          className="rounded-lg bg-green-600 px-5 py-2.5 text-sm font-medium hover:bg-green-500 disabled:opacity-50"
        >
          Happy Path
        </button>
        <button
          onClick={() => runDemo("attack")}
          disabled={running}
          className="rounded-lg bg-red-600 px-5 py-2.5 text-sm font-medium hover:bg-red-500 disabled:opacity-50"
        >
          Attack Path
        </button>
      </div>

      {/* Steps progress */}
      {steps.length > 0 && (
        <ol className="space-y-2 text-sm">
          {steps.map((s, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="shrink-0 mt-0.5">
                {s.status === "done" && (
                  <span className="text-green-400">✓</span>
                )}
                {s.status === "running" && (
                  <span className="text-yellow-400 animate-pulse">●</span>
                )}
                {s.status === "pending" && (
                  <span className="text-gray-600">○</span>
                )}
                {s.status === "error" && (
                  <span className="text-red-400">✗</span>
                )}
              </span>
              <span>
                <span className="font-medium">{s.label}</span>
                {s.detail && (
                  <span className="ml-2 text-gray-400">— {s.detail}</span>
                )}
              </span>
            </li>
          ))}
        </ol>
      )}

      {/* Policy decisions */}
      {decisions.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
            Policy Decisions
          </h3>
          {decisions.map((d, i) => (
            <div
              key={i}
              className={`rounded-lg border p-3 text-sm ${
                d.decision === "ALLOW"
                  ? "border-green-500/50 bg-green-500/5 text-green-300"
                  : "border-red-500/50 bg-red-500/5 text-red-300"
              }`}
            >
              <span className="font-semibold">{d.decision}</span> —{" "}
              {d.action_type}: {d.reason}
            </div>
          ))}
        </div>
      )}

      {/* Timeline */}
      {timeline.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
            Event Timeline
          </h3>
          <Timeline events={timeline} />
        </div>
      )}

      {/* Verification badge */}
      {verified !== null && (
        <div
          className={`inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-semibold ${
            verified
              ? "bg-green-500/20 text-green-400 border border-green-500"
              : "bg-red-500/20 text-red-400 border border-red-500"
          }`}
        >
          {verified ? "✓ Receipt Verified" : "✗ Verification Failed"}
        </div>
      )}
    </div>
  );
}

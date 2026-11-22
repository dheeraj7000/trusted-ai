"use client";

import { useState } from "react";
import type { Scorecard, ScenarioResult } from "@/lib/api";
import { runBenchmarks } from "@/lib/api";

const METRIC_LABELS: Record<string, string> = {
  task_success_rate: "Task Success",
  policy_adherence_rate: "Policy Adherence",
  unauthorized_action_count: "Unauthorized Actions",
  evidence_integrity_rate: "Evidence Integrity",
  state_verification_rate: "State Verification",
  p95_latency_ms: "P95 Latency (ms)",
  cost_per_verified_task: "Cost / Task",
};

function MetricCard({ label, value }: { label: string; value: number }) {
  const isPercent =
    label.includes("Rate") || label.includes("Success") || label.includes("Verification");
  const display = isPercent ? `${value.toFixed(1)}%` : value.toFixed(2);

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-3 text-center">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className="text-lg font-semibold">{display}</p>
    </div>
  );
}

function ResultRow({ r }: { r: ScenarioResult }) {
  return (
    <tr className={r.passed ? "bg-green-500/5" : "bg-red-500/5"}>
      <td className="px-3 py-2 text-sm">{r.scenario_name}</td>
      <td className="px-3 py-2 text-sm text-center">
        {r.policy_adherence ? (
          <span className="text-green-400">✓</span>
        ) : (
          <span className="text-red-400">✗</span>
        )}
      </td>
      <td className="px-3 py-2 text-sm text-center">
        {r.evidence_integrity ? (
          <span className="text-green-400">✓</span>
        ) : (
          <span className="text-red-400">✗</span>
        )}
      </td>
      <td className="px-3 py-2 text-sm text-center font-mono">
        {r.latency_ms.toFixed(1)}
      </td>
      <td className="px-3 py-2 text-sm text-center">
        {r.passed ? (
          <span className="rounded bg-green-500/20 px-2 py-0.5 text-xs font-semibold text-green-400">
            PASS
          </span>
        ) : (
          <span className="rounded bg-red-500/20 px-2 py-0.5 text-xs font-semibold text-red-400">
            FAIL
          </span>
        )}
      </td>
    </tr>
  );
}

export default function BenchmarkPanel() {
  const [scorecard, setScorecard] = useState<Scorecard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const sc = await runBenchmarks();
      setScorecard(sc);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Benchmark run failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <button
        onClick={handleRun}
        disabled={loading}
        className="rounded-lg bg-purple-600 px-5 py-2.5 text-sm font-medium hover:bg-purple-500 disabled:opacity-50"
      >
        {loading ? "Running…" : "Run Benchmarks"}
      </button>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {scorecard && (
        <>
          {/* Summary */}
          <div className="flex items-center gap-4 text-sm">
            <span>
              <span className="text-green-400 font-semibold">
                {scorecard.passed}
              </span>{" "}
              passed
            </span>
            <span>
              <span className="text-red-400 font-semibold">
                {scorecard.failed}
              </span>{" "}
              failed
            </span>
            <span className="text-gray-500">
              / {scorecard.total_scenarios} total
            </span>
          </div>

          {/* Metrics grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(scorecard.scores).map(([key, value]) => (
              <MetricCard
                key={key}
                label={METRIC_LABELS[key] ?? key}
                value={value}
              />
            ))}
          </div>

          {/* Results table */}
          <div className="overflow-x-auto rounded-lg border border-gray-800">
            <table className="w-full text-left">
              <thead className="bg-gray-900 text-xs uppercase text-gray-400">
                <tr>
                  <th className="px-3 py-2">Scenario</th>
                  <th className="px-3 py-2 text-center">Policy</th>
                  <th className="px-3 py-2 text-center">Evidence</th>
                  <th className="px-3 py-2 text-center">Latency (ms)</th>
                  <th className="px-3 py-2 text-center">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {scorecard.results.map((r) => (
                  <ResultRow key={r.scenario_id} r={r} />
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

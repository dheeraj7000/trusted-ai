"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart3,
  CheckCircle,
  XCircle,
  TrendingUp,
  Shield,
  Zap,
  Loader2,
} from "lucide-react";
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

function StatCard({
  label,
  value,
  color,
  delay,
}: {
  label: string;
  value: string;
  color: string;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="glass-card p-5 text-center"
    >
      <p className="text-xs text-gray-500 mb-2 uppercase tracking-wider">
        {label}
      </p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
    </motion.div>
  );
}

function MetricBar({
  label,
  value,
  delay,
}: {
  label: string;
  value: number;
  delay: number;
}) {
  const isPercent = label.includes("Rate") || label.includes("Success") || label.includes("Verification") || label.includes("Integrity");
  const display = isPercent ? `${value.toFixed(1)}%` : value.toFixed(2);
  const barWidth = isPercent ? Math.min(value, 100) : Math.min((value / 100) * 100, 100);
  const barColor =
    value >= 90
      ? "bg-accent-500"
      : value >= 70
        ? "bg-yellow-500"
        : "bg-danger-500";

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.4 }}
    >
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-sm text-gray-400">{label}</span>
        <span className="text-sm font-semibold text-white">{display}</span>
      </div>
      <div className="h-2 rounded-full bg-gray-800 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${barWidth}%` }}
          transition={{ delay: delay + 0.2, duration: 0.8, ease: "easeOut" }}
          className={`h-full rounded-full ${barColor}`}
        />
      </div>
    </motion.div>
  );
}

function ResultRow({ r, index }: { r: ScenarioResult; index: number }) {
  return (
    <motion.tr
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: index * 0.05 }}
      className={r.passed ? "bg-accent-500/5" : "bg-danger-500/5"}
    >
      <td className="px-4 py-3 text-sm text-gray-200">{r.scenario_name}</td>
      <td className="px-4 py-3 text-sm text-center">
        {r.policy_adherence ? (
          <CheckCircle className="h-4 w-4 text-accent-400 inline" />
        ) : (
          <XCircle className="h-4 w-4 text-danger-400 inline" />
        )}
      </td>
      <td className="px-4 py-3 text-sm text-center">
        {r.evidence_integrity ? (
          <CheckCircle className="h-4 w-4 text-accent-400 inline" />
        ) : (
          <XCircle className="h-4 w-4 text-danger-400 inline" />
        )}
      </td>
      <td className="px-4 py-3 text-sm text-center font-mono text-gray-400">
        {r.latency_ms.toFixed(1)}
      </td>
      <td className="px-4 py-3 text-sm text-center">
        {r.passed ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-accent-500/20 px-2.5 py-0.5 text-xs font-semibold text-accent-400">
            PASS
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 rounded-full bg-danger-500/20 px-2.5 py-0.5 text-xs font-semibold text-danger-400">
            FAIL
          </span>
        )}
      </td>
    </motion.tr>
  );
}

export default function BenchmarkPanel({
  scorecard,
  onScorecard,
}: {
  scorecard: Scorecard | null;
  onScorecard: (s: Scorecard) => void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const sc = await runBenchmarks();
      onScorecard(sc);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Benchmark run failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="text-center">
        <button
          onClick={handleRun}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl bg-brand-500 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-brand-500/25 hover:bg-brand-600 disabled:opacity-50 transition-all duration-300"
        >
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <BarChart3 className="h-5 w-5" />
          )}
          {loading ? "Running Benchmarks..." : "Run Trust Benchmarks"}
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-danger-500/30 bg-danger-500/5 p-4 text-center">
          <p className="text-sm text-danger-400">{error}</p>
        </div>
      )}

      <AnimatePresence>
        {scorecard && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
          >
            {/* Summary stats */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <StatCard
                label="Scenarios Passed"
                value={`${scorecard.passed}/${scorecard.total_scenarios}`}
                color="text-accent-400"
                delay={0}
              />
              <StatCard
                label="Policy Adherence"
                value={`${(scorecard.scores.policy_adherence_rate ?? 0).toFixed(0)}%`}
                color="text-brand-400"
                delay={0.1}
              />
              <StatCard
                label="Unauthorized Actions"
                value={`${scorecard.scores.unauthorized_action_count ?? 0}`}
                color={
                  (scorecard.scores.unauthorized_action_count ?? 0) === 0
                    ? "text-accent-400"
                    : "text-danger-400"
                }
                delay={0.2}
              />
            </div>

            {/* Metric bars */}
            <div className="glass-card p-6 space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="h-4 w-4 text-brand-400" />
                <h3 className="text-sm font-semibold text-white">
                  Detailed Metrics
                </h3>
              </div>
              {Object.entries(scorecard.scores).map(([key, value], i) => (
                <MetricBar
                  key={key}
                  label={METRIC_LABELS[key] ?? key}
                  value={value}
                  delay={i * 0.1}
                />
              ))}
            </div>

            {/* Results table */}
            <div className="glass-card overflow-hidden">
              <div className="flex items-center gap-2 px-6 py-4 border-b border-gray-800/50">
                <Shield className="h-4 w-4 text-brand-400" />
                <h3 className="text-sm font-semibold text-white">
                  Scenario Results
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-gray-900/50 text-xs uppercase text-gray-500">
                    <tr>
                      <th className="px-4 py-3">Scenario</th>
                      <th className="px-4 py-3 text-center">Policy</th>
                      <th className="px-4 py-3 text-center">Evidence</th>
                      <th className="px-4 py-3 text-center">Latency</th>
                      <th className="px-4 py-3 text-center">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/50">
                    {scorecard.results.map((r, i) => (
                      <ResultRow key={r.scenario_id} r={r} index={i} />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
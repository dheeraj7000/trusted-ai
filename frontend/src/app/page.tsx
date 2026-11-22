"use client";

import { useState } from "react";
import type { ProofReceipt } from "@/lib/api";
import DemoFlow from "@/components/DemoFlow";
import ProofReceiptCard from "@/components/ProofReceipt";
import BenchmarkPanel from "@/components/BenchmarkPanel";

type Tab = "demo" | "receipts" | "benchmarks";

export default function Home() {
  const [tab, setTab] = useState<Tab>("demo");
  const [latestReceipt, setLatestReceipt] = useState<ProofReceipt | null>(
    null,
  );

  const tabs: { id: Tab; label: string }[] = [
    { id: "demo", label: "Demo" },
    { id: "receipts", label: "Receipts" },
    { id: "benchmarks", label: "Benchmarks" },
  ];

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">
          AgentProof
        </h1>
        <p className="mt-1 text-gray-400">
          Verifiable AI Agent Firewall — tamper-evident audit receipts for every
          agent action.
        </p>
      </header>

      {/* Tab navigation */}
      <nav className="mb-6 flex gap-1 rounded-lg bg-gray-900 p-1" role="tablist">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition ${
              tab === t.id
                ? "bg-gray-800 text-white shadow"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {/* Tab panels */}
      <div role="tabpanel">
        {tab === "demo" && <DemoFlow onReceipt={setLatestReceipt} />}
        {tab === "receipts" && <ProofReceiptCard receipt={latestReceipt} />}
        {tab === "benchmarks" && <BenchmarkPanel />}
      </div>
    </main>
  );
}

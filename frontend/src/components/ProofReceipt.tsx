"use client";

import { useState } from "react";
import type { ProofReceipt as Receipt, VerificationResult } from "@/lib/api";
import { verifyReceipt } from "@/lib/api";

function truncHash(hash: string): string {
  if (hash.length <= 16) return hash;
  return `${hash.slice(0, 8)}…${hash.slice(-8)}`;
}

function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-gray-400 text-xs w-40 shrink-0">{label}</span>
      <code className="text-xs truncate flex-1" title={value}>
        {truncHash(value)}
      </code>
      <button
        onClick={copy}
        className="text-xs text-blue-400 hover:text-blue-300 shrink-0"
        aria-label={`Copy ${label}`}
      >
        {copied ? "Copied" : "Copy"}
      </button>
    </div>
  );
}

export default function ProofReceiptCard({
  receipt,
}: {
  receipt: Receipt | null;
}) {
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [tampered, setTampered] = useState(false);

  if (!receipt) {
    return (
      <p className="text-sm text-gray-500 italic">
        No receipt available. Run a demo first.
      </p>
    );
  }

  const handleVerify = async () => {
    setLoading(true);
    try {
      const r = await verifyReceipt(receipt);
      setResult(r);
      setTampered(false);
    } catch {
      setResult({ valid: false, checks: {}, errors: ["Request failed"] });
    } finally {
      setLoading(false);
    }
  };

  const handleTamper = async () => {
    setLoading(true);
    try {
      const tamperReceipt = {
        ...receipt,
        provenance_root:
          receipt.provenance_root.charAt(0) === "a"
            ? "b" + receipt.provenance_root.slice(1)
            : "a" + receipt.provenance_root.slice(1),
      };
      const r = await verifyReceipt(tamperReceipt);
      setResult(r);
      setTampered(true);
    } catch {
      setResult({ valid: false, checks: {}, errors: ["Request failed"] });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-4">
      {/* Identity */}
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
          Identity
        </h3>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <dt className="text-gray-400">Agent ID</dt>
          <dd>{receipt.agent_id}</dd>
          <dt className="text-gray-400">Model Provider</dt>
          <dd>{receipt.model_provider}</dd>
          <dt className="text-gray-400">Model ID</dt>
          <dd>{receipt.model_id}</dd>
        </dl>
      </section>

      {/* Policy */}
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
          Policy
        </h3>
        <p className="text-sm">{receipt.policy_version}</p>
      </section>

      {/* Evidence Roots */}
      <section className="space-y-1">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
          Evidence Roots
        </h3>
        <CopyField label="Provenance Root" value={receipt.provenance_root} />
        <CopyField label="Trace Root" value={receipt.trace_root} />
        <CopyField label="State Root" value={receipt.state_root} />
      </section>

      {/* Verification */}
      <section className="space-y-1">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
          Verification
        </h3>
        <CopyField label="Receipt Root" value={receipt.receipt_root} />
        <CopyField label="Signature" value={receipt.signature} />
        <div className="flex items-center justify-between gap-2">
          <span className="text-gray-400 text-xs w-40 shrink-0">Key ID</span>
          <code className="text-xs truncate flex-1">{receipt.key_id}</code>
        </div>
      </section>

      {/* Metadata */}
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
          Metadata
        </h3>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <dt className="text-gray-400">Timestamp</dt>
          <dd className="font-mono text-xs">{receipt.timestamp}</dd>
          <dt className="text-gray-400">Version</dt>
          <dd>{receipt.receipt_version}</dd>
        </dl>
      </section>

      {/* Actions */}
      <div className="flex gap-3 pt-2">
        <button
          onClick={handleVerify}
          disabled={loading}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium hover:bg-blue-500 disabled:opacity-50"
        >
          {loading ? "Verifying…" : "Verify"}
        </button>
        <button
          onClick={handleTamper}
          disabled={loading}
          className="rounded-lg bg-yellow-600 px-4 py-2 text-sm font-medium hover:bg-yellow-500 disabled:opacity-50"
        >
          Tamper Demo
        </button>
      </div>

      {/* Result badge */}
      {result && (
        <div
          className={`mt-2 inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-semibold ${
            result.valid
              ? "bg-green-500/20 text-green-400 border border-green-500"
              : "bg-red-500/20 text-red-400 border border-red-500"
          }`}
        >
          {result.valid ? "✓ VALID" : "✗ INVALID"}
          {tampered && !result.valid && (
            <span className="text-xs font-normal opacity-75">
              (tampered provenance_root)
            </span>
          )}
        </div>
      )}
    </div>
  );
}

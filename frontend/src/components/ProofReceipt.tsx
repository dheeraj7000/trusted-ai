"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield,
  FileText,
  Database,
  Lock,
  CheckCircle,
  XCircle,
  Copy,
  Check,
  AlertTriangle,
} from "lucide-react";
import type { ProofReceipt as Receipt, VerificationResult } from "@/lib/api";
import { verifyReceipt } from "@/lib/api";

function truncHash(hash: string): string {
  if (hash.length <= 16) return hash;
  return `${hash.slice(0, 8)}...${hash.slice(-8)}`;
}

function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div className="flex items-center justify-between gap-2 py-1.5">
      <span className="text-gray-500 text-xs w-36 shrink-0">{label}</span>
      <code className="text-xs text-gray-300 truncate flex-1 font-mono" title={value}>
        {truncHash(value)}
      </code>
      <button
        onClick={copy}
        className="text-gray-500 hover:text-brand-400 shrink-0 transition-colors"
        aria-label={`Copy ${label}`}
      >
        {copied ? (
          <Check className="h-3.5 w-3.5 text-accent-400" />
        ) : (
          <Copy className="h-3.5 w-3.5" />
        )}
      </button>
    </div>
  );
}

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-brand-400" />
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
          {title}
        </h3>
      </div>
      {children}
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
      <div className="glass-card p-8 text-center">
        <Lock className="h-8 w-8 text-gray-600 mx-auto mb-3" />
        <p className="text-sm text-gray-500">
          No receipt available. Run a demo first.
        </p>
      </div>
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
    <div className="mx-auto max-w-2xl">
      <div className="glass-card overflow-hidden">
        {/* Certificate header */}
        <div className="border-b border-gray-800/50 bg-gray-900/50 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="h-5 w-5 text-brand-400" />
              <div>
                <h3 className="text-sm font-semibold text-white">
                  Proof Receipt
                </h3>
                <p className="text-xs text-gray-500 font-mono">
                  {receipt.run_id}
                </p>
              </div>
            </div>
            <span className="rounded-full border border-gray-700 bg-gray-800 px-3 py-1 text-xs text-gray-400">
              v{receipt.receipt_version}
            </span>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          <Section icon={Shield} title="Identity">
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
              <dt className="text-gray-500">Agent ID</dt>
              <dd className="text-gray-200">{receipt.agent_id}</dd>
              <dt className="text-gray-500">Model</dt>
              <dd className="text-gray-200">
                {receipt.model_provider}/{receipt.model_id}
              </dd>
            </dl>
          </Section>

          <Section icon={FileText} title="Policy">
            <p className="text-sm text-gray-200">{receipt.policy_version}</p>
          </Section>

          <Section icon={Database} title="Evidence Roots">
            <div className="space-y-0.5">
              <CopyField
                label="Provenance Root"
                value={receipt.provenance_root}
              />
              <CopyField label="Trace Root" value={receipt.trace_root} />
              <CopyField label="State Root" value={receipt.state_root} />
            </div>
          </Section>

          <Section icon={Lock} title="Cryptography">
            <div className="space-y-0.5">
              <CopyField label="Receipt Root" value={receipt.receipt_root} />
              <CopyField label="Signature" value={receipt.signature} />
              <div className="flex items-center justify-between gap-2 py-1.5">
                <span className="text-gray-500 text-xs w-36 shrink-0">
                  Key ID
                </span>
                <code className="text-xs text-gray-300 truncate flex-1 font-mono">
                  {receipt.key_id}
                </code>
              </div>
            </div>
          </Section>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={handleVerify}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-brand-500 px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50 transition-colors"
            >
              <CheckCircle className="h-4 w-4" />
              Verify Integrity
            </button>
            <button
              onClick={handleTamper}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl border border-yellow-500/30 bg-yellow-500/10 px-5 py-2.5 text-sm font-medium text-yellow-400 hover:bg-yellow-500/20 disabled:opacity-50 transition-colors"
            >
              <AlertTriangle className="h-4 w-4" />
              Tamper with Evidence
            </button>
          </div>

          {/* Verification result */}
          <AnimatePresence mode="wait">
            {result && (
              <motion.div
                key={result.valid ? "valid" : "invalid"}
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                transition={{ type: "spring", duration: 0.5 }}
                className={`flex items-center justify-center gap-3 rounded-xl border p-4 ${
                  result.valid
                    ? "border-accent-500/50 bg-accent-500/10 glow-green"
                    : "border-danger-500/50 bg-danger-500/10 glow-red"
                }`}
              >
                {result.valid ? (
                  <>
                    <CheckCircle className="h-6 w-6 text-accent-400" />
                    <span className="text-lg font-bold text-accent-400">
                      VERIFIED
                    </span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-6 w-6 text-danger-400" />
                    <span className="text-lg font-bold text-danger-400">
                      INVALID
                    </span>
                    {tampered && (
                      <span className="text-xs text-danger-400/70">
                        (tampered provenance_root detected)
                      </span>
                    )}
                  </>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Shield, Zap, Lock, BarChart3, DollarSign } from "lucide-react";
import type { ProofReceipt, TimelineEvent, Scorecard } from "@/lib/api";
import DemoFlow from "@/components/DemoFlow";
import Timeline from "@/components/Timeline";
import ProofReceiptCard from "@/components/ProofReceipt";
import BenchmarkPanel from "@/components/BenchmarkPanel";
import BusinessValue from "@/components/BusinessValue";

const sectionVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
};

export default function Home() {
  const [latestReceipt, setLatestReceipt] = useState<ProofReceipt | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [scorecard, setScorecard] = useState<Scorecard | null>(null);

  const demoRef = useRef<HTMLDivElement>(null);

  const scrollToDemo = () => {
    demoRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-brand-900/20 via-gray-950 to-gray-950" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.1),transparent_60%)]" />

        <div className="relative mx-auto max-w-6xl px-6 pb-20 pt-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-4 py-1.5 text-sm text-brand-300">
              <Shield className="h-4 w-4" />
              AI Agent Security Platform
            </div>

            <h1 className="mb-6 text-5xl font-bold tracking-tight text-white md:text-7xl">
              <span className="gradient-text">AgentProof</span>
            </h1>

            <p className="mx-auto mb-4 max-w-2xl text-xl text-gray-300 md:text-2xl text-balance">
              Block unsafe AI agent actions. Prove what happened.
            </p>
            <p className="mx-auto mb-10 max-w-xl text-base text-gray-500">
              Tamper-evident audit receipts for every agent action. Policy enforcement in &lt;100ms.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-4">
              <button
                onClick={scrollToDemo}
                className="group inline-flex items-center gap-2 rounded-xl bg-accent-500 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-accent-500/25 hover:bg-accent-600 hover:shadow-accent-500/40 transition-all duration-300"
              >
                <Zap className="h-5 w-5" />
                Run Safe Transaction
              </button>
              <button
                onClick={scrollToDemo}
                className="group inline-flex items-center gap-2 rounded-xl bg-danger-500 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-danger-500/25 hover:bg-danger-600 hover:shadow-danger-500/40 transition-all duration-300"
              >
                <Shield className="h-5 w-5" />
                Simulate Attack
              </button>
            </div>
          </motion.div>

          {/* Feature pills */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="mt-16 flex flex-wrap items-center justify-center gap-6 text-sm text-gray-400"
          >
            {[
              { icon: Shield, text: "Policy Engine" },
              { icon: Lock, text: "Cryptographic Receipts" },
              { icon: BarChart3, text: "Trust Benchmarks" },
              { icon: DollarSign, text: "$0.001 per verified action" },
            ].map((f) => (
              <div key={f.text} className="flex items-center gap-2">
                <f.icon className="h-4 w-4 text-brand-400" />
                {f.text}
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Demo Flow Section */}
      <motion.section
        ref={demoRef}
        variants={sectionVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        className="mx-auto max-w-6xl px-6 py-16"
      >
        <div className="mb-8 text-center">
          <h2 className="text-3xl font-bold text-white">Live Demo</h2>
          <p className="mt-2 text-gray-400">
            Watch AgentProof evaluate and enforce policies in real-time
          </p>
        </div>
        <DemoFlow
          onReceipt={setLatestReceipt}
          onTimeline={setTimeline}
        />
      </motion.section>

      {/* Timeline Section */}
      <AnimatePresence>
        {timeline.length > 0 && (
          <motion.section
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
            exit={{ opacity: 0 }}
            className="mx-auto max-w-6xl px-6 py-16"
          >
            <div className="mb-8 text-center">
              <h2 className="text-3xl font-bold text-white">Event Timeline</h2>
              <p className="mt-2 text-gray-400">
                Every action recorded with cryptographic proof
              </p>
            </div>
            <Timeline events={timeline} />
          </motion.section>
        )}
      </AnimatePresence>

      {/* Proof Receipt Section */}
      <AnimatePresence>
        {latestReceipt && (
          <motion.section
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
            exit={{ opacity: 0 }}
            className="mx-auto max-w-6xl px-6 py-16"
          >
            <div className="mb-8 text-center">
              <h2 className="text-3xl font-bold text-white">Proof Receipt</h2>
              <p className="mt-2 text-gray-400">
                Tamper-evident cryptographic certificate
              </p>
            </div>
            <ProofReceiptCard receipt={latestReceipt} />
          </motion.section>
        )}
      </AnimatePresence>

      {/* Benchmark Section */}
      <motion.section
        variants={sectionVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        className="mx-auto max-w-6xl px-6 py-16"
      >
        <div className="mb-8 text-center">
          <h2 className="text-3xl font-bold text-white">Trust Benchmarks</h2>
          <p className="mt-2 text-gray-400">
            Comprehensive security scoring across attack scenarios
          </p>
        </div>
        <BenchmarkPanel scorecard={scorecard} onScorecard={setScorecard} />
      </motion.section>

      {/* Business Value Section */}
      <motion.section
        variants={sectionVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        className="mx-auto max-w-6xl px-6 py-16"
      >
        <BusinessValue />
      </motion.section>

      {/* Footer */}
      <footer className="border-t border-gray-800/50 py-8 text-center text-sm text-gray-500">
        <p>&copy; 2025 AgentProof. Verifiable AI Agent Security.</p>
      </footer>
    </main>
  );
}
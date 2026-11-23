"use client";

import { motion } from "framer-motion";
import {
  Shield,
  Zap,
  CheckCircle,
  Landmark,
  Heart,
  Scale,
  ShoppingCart,
  Star,
  Clock,
  DollarSign,
  Lock,
  Globe,
} from "lucide-react";

const tiers = [
  {
    name: "Starter",
    price: "$99",
    period: "/mo",
    features: [
      "1,000 verified actions/mo",
      "Standard policy rules",
      "Email support",
      "Basic audit dashboard",
    ],
    popular: false,
  },
  {
    name: "Pro",
    price: "$499",
    period: "/mo",
    features: [
      "50,000 verified actions/mo",
      "Custom policy rules",
      "Priority support",
      "Full audit trail & analytics",
      "Team management",
    ],
    popular: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    features: [
      "Unlimited verified actions",
      "AWS KMS integration",
      "SSO & RBAC",
      "99.99% SLA",
      "Dedicated support",
      "On-prem deployment",
    ],
    popular: false,
  },
];

const useCases = [
  {
    icon: Landmark,
    title: "Financial Services",
    desc: "Prevent unauthorized transactions and ensure regulatory compliance for AI-driven trading and operations.",
  },
  {
    icon: Heart,
    title: "Healthcare",
    desc: "Protect patient data and ensure HIPAA compliance when AI agents access medical records.",
  },
  {
    icon: Scale,
    title: "Legal",
    desc: "Maintain chain of custody for AI-generated legal documents with tamper-evident receipts.",
  },
  {
    icon: ShoppingCart,
    title: "E-commerce",
    desc: "Guard against fraudulent refunds, data exfiltration, and policy-violating AI actions.",
  },
];

const trustBadges = [
  { icon: Shield, text: "SOC 2 Ready" },
  { icon: Heart, text: "HIPAA Compatible" },
  { icon: Globe, text: "EU AI Act Aligned" },
];

export default function BusinessValue() {
  return (
    <div className="space-y-20">
      {/* Section header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-white md:text-4xl">
          Why AgentProof?
        </h2>
        <p className="mt-3 text-lg text-gray-400 max-w-2xl mx-auto">
          As AI agents handle real transactions, the cost of unverified actions grows exponentially.
          AgentProof makes every action auditable.
        </p>
      </div>

      {/* ROI metrics */}
      <div className="grid gap-6 md:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="glass-card p-6 text-center"
        >
          <DollarSign className="h-8 w-8 text-danger-400 mx-auto mb-3" />
          <p className="text-3xl font-bold text-white mb-2">$50,000+</p>
          <p className="text-sm text-gray-400">
            Average cost of a single unauthorized AI agent action
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="glass-card p-6 text-center"
        >
          <Clock className="h-8 w-8 text-brand-400 mx-auto mb-3" />
          <p className="text-3xl font-bold text-white mb-2">&lt;100ms</p>
          <p className="text-sm text-gray-400">
            Policy evaluation latency per action
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="glass-card p-6 text-center"
        >
          <Zap className="h-8 w-8 text-accent-400 mx-auto mb-3" />
          <p className="text-3xl font-bold text-white mb-2">$0.001</p>
          <p className="text-sm text-gray-400">
            Per verified action with cryptographic proof
          </p>
        </motion.div>
      </div>

      {/* Pricing tiers */}
      <div>
        <h3 className="text-2xl font-bold text-white text-center mb-8">
          Pricing
        </h3>
        <div className="grid gap-6 md:grid-cols-3">
          {tiers.map((tier, i) => (
            <motion.div
              key={tier.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className={`relative glass-card p-6 ${
                tier.popular
                  ? "border-brand-500/50 ring-1 ring-brand-500/20"
                  : ""
              }`}
            >
              {tier.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="inline-flex items-center gap-1 rounded-full bg-brand-500 px-3 py-1 text-xs font-semibold text-white">
                    <Star className="h-3 w-3" />
                    Most Popular
                  </span>
                </div>
              )}
              <div className="text-center mb-6">
                <h4 className="text-lg font-semibold text-white mb-2">
                  {tier.name}
                </h4>
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-4xl font-bold text-white">
                    {tier.price}
                  </span>
                  {tier.period && (
                    <span className="text-gray-500">{tier.period}</span>
                  )}
                </div>
              </div>
              <ul className="space-y-3 mb-6">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-gray-300">
                    <CheckCircle className="h-4 w-4 text-accent-400 flex-shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              <button
                className={`w-full rounded-xl py-2.5 text-sm font-semibold transition-colors ${
                  tier.popular
                    ? "bg-brand-500 text-white hover:bg-brand-600"
                    : "border border-gray-700 text-gray-300 hover:border-gray-600 hover:text-white"
                }`}
              >
                Get Started
              </button>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Use cases */}
      <div>
        <h3 className="text-2xl font-bold text-white text-center mb-8">
          Built For
        </h3>
        <div className="grid gap-6 md:grid-cols-2">
          {useCases.map((uc, i) => (
            <motion.div
              key={uc.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass-card-hover p-6"
            >
              <div className="flex items-start gap-4">
                <div className="rounded-xl bg-brand-500/10 border border-brand-500/20 p-3">
                  <uc.icon className="h-6 w-6 text-brand-400" />
                </div>
                <div>
                  <h4 className="text-base font-semibold text-white mb-1">
                    {uc.title}
                  </h4>
                  <p className="text-sm text-gray-400">{uc.desc}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Trust badges */}
      <div className="flex flex-wrap items-center justify-center gap-6">
        {trustBadges.map((badge) => (
          <div
            key={badge.text}
            className="inline-flex items-center gap-2 rounded-full border border-gray-700/50 bg-gray-800/50 px-5 py-2.5 text-sm text-gray-400"
          >
            <badge.icon className="h-4 w-4 text-brand-400" />
            {badge.text}
          </div>
        ))}
      </div>
    </div>
  );
}
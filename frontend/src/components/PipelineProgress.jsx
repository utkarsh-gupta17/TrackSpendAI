import React, { useState, useEffect } from 'react';
import { CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react';

const STEPS = [
  { id: 1, label: 'Parsing statement', icon: '📄' },
  { id: 2, label: 'Categorising transactions', icon: '🏷️' },
  { id: 3, label: 'Scanning for anomalies', icon: '🔍' },
  { id: 4, label: 'Retrieving financial guidance', icon: '📚' },
  { id: 5, label: 'Generating your report', icon: '✨' },
];

const FACTS = [
  "The 50/30/20 rule: 50% on needs, 30% on wants, 20% on savings.",
  "Section 80C allows up to ₹1.5 lakh tax deduction — PPF and ELSS qualify.",
  "An emergency fund should cover 3-6 months of your expenses.",
  "Starting a ₹5,000 SIP at 25 vs 35 can mean ₹1 crore more at retirement.",
  "Health insurance premiums up to ₹25,000 are deductible under Section 80D.",
];

export default function PipelineProgress({ progress }) {
  const [factIndex, setFactIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setFactIndex((prev) => (prev + 1) % FACTS.length);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  const currentStep = progress?.step || 1;
  const overallProgress = (currentStep / STEPS.length) * 100;

  return (
    <div className="max-w-2xl mx-auto py-12">
      {/* Progress Bar */}
      <div className="h-1.5 w-full bg-border rounded-full mb-12 overflow-hidden">
        <div 
          className="h-full bg-accent transition-all duration-500 ease-out"
          style={{ width: `${overallProgress}%` }}
        />
      </div>

      <div className="space-y-6">
        {STEPS.map((step) => {
          const isActive = progress?.step === step.id;
          const isDone = progress?.step > step.id || (progress?.step === step.id && progress?.status === 'done');
          const isFuture = progress?.step < step.id;

          return (
            <div 
              key={step.id}
              className={`flex items-center gap-6 p-6 rounded-3xl border transition-all duration-300 ${
                isActive ? 'bg-accent/5 border-accent scale-105 shadow-xl shadow-accent/10' : 
                isDone ? 'bg-card border-border opacity-60' : 
                'bg-card/50 border-border opacity-40 grayscale'
              }`}
            >
              <div className="text-3xl">{step.icon}</div>
              <div className="flex-1">
                <h3 className={`font-bold text-lg ${isActive ? 'text-white' : 'text-gray-400'}`}>
                  {step.label}
                </h3>
                {isActive && progress.message && (
                  <p className="text-accent text-sm mt-1 animate-pulse">{progress.message}</p>
                )}
                {isDone && (
                   <p className="text-green-500 text-sm mt-1">Completed</p>
                )}
              </div>
              <div>
                {isDone ? (
                  <CheckCircle2 className="w-6 h-6 text-green-500" />
                ) : isActive ? (
                  <Loader2 className="w-6 h-6 text-accent animate-spin" />
                ) : (
                  <Circle className="w-6 h-6 text-gray-700" />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Facts Carousel */}
      <div className="mt-16 p-8 bg-card border border-border rounded-3xl text-center relative overflow-hidden group">
        <div className="absolute top-0 left-0 w-1 h-full bg-accent"></div>
        <p className="text-accent font-bold text-xs uppercase tracking-widest mb-3">Did you know?</p>
        <p className="text-gray-300 text-lg transition-all duration-500">
          {FACTS[factIndex]}
        </p>
      </div>
    </div>
  );
}

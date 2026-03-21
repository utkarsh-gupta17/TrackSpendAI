import React from 'react';
import { Sparkles, ExternalLink, ShieldCheck } from 'lucide-react';

const RecommendationCard = ({ rec }) => {
  const [isFlipped, setIsFlipped] = React.useState(false);

  return (
    <div className="relative w-full group grid h-full" style={{ perspective: '1000px' }}>
      <div
        className="w-full relative transition-all duration-700 ease-in-out grid col-start-1 row-start-1 h-full"
        style={{ transformStyle: 'preserve-3d', transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)' }}
      >
        {/* Front */}
        <div
          className="bg-card border border-border p-8 rounded-3xl hover:border-accent/40 col-start-1 row-start-1 flex flex-col h-full"
          style={{ backfaceVisibility: 'hidden' }}
        >
          <div className="flex justify-between items-start mb-4">
            <span className={`text-[10px] font-bold uppercase tracking-tighter px-2 py-1 rounded-md ${rec.priority === 'high' ? 'bg-red-500/20 text-red-500' : 'bg-blue-500/20 text-blue-500'
              }`}>
              {rec.priority || 'low'} Priority
            </span>
            <span className="text-[10px] font-bold text-gray-500 bg-border px-2 py-1 rounded-md flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" /> {rec.source || 'General Finance'}
            </span>
          </div>
          <h4 className="text-lg font-bold mb-3 leading-tight">{rec.title || 'Guideline'}</h4>
          <div className="flex-grow">
            <p className="text-gray-400 text-sm leading-relaxed">{rec.action || rec.detail || 'Action details not available.'}</p>
          </div>
          <button
            onClick={() => setIsFlipped(true)}
            className="mt-6 self-start text-xs font-bold text-accent hover:text-white transition-colors flex items-center gap-2 bg-accent/10 px-4 py-2 rounded-xl"
          >
            Why this reason? &rarr;
          </button>
        </div>

        {/* Back */}
        <div
          className="bg-accent/5 border border-accent/30 p-8 rounded-3xl col-start-1 row-start-1 flex flex-col h-full"
          style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
        >
          <div className="flex items-center gap-2 mb-4 text-accent">
            <Sparkles className="w-5 h-5" />
            <h4 className="font-bold text-lg">The "Why"</h4>
          </div>
          <div className="flex-grow">
            <p className="text-gray-300 text-sm leading-relaxed">
              {rec.reason || 'We determined this from a holistic analysis of your recent spending habits and anomalies.'}
            </p>
          </div>
          <button
            onClick={() => setIsFlipped(false)}
            className="mt-6 self-start text-xs font-bold text-gray-400 hover:text-white transition-colors flex items-center gap-2 border border-border/50 px-4 py-2 rounded-xl hover:bg-card hover:border-border"
          >
            &larr; Back to Insight
          </button>
        </div>
      </div>
    </div>
  );
};

export default function InsightsPanel({ report }) {
  if (!report) return null;

  const {
    headline = 'Financial Analysis Ready',
    health_label = 'N/A',
    health_score = 0,
    top_insights = [],
    recommendations = [],
  } = report;

  return (
    <div className="space-y-8 mt-8">
      {/* AI Headline */}
      <div className="bg-gradient-to-br from-accent/20 to-accent/5 border border-accent/20 p-10 rounded-[3rem] shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10">
          <Sparkles className="w-32 h-32 text-accent" />
        </div>
        <div className="flex items-center gap-3 mb-6">
          <span className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest ${health_label === 'Excellent' ? 'bg-green-500/20 text-green-500' :
              health_label === 'Good' ? 'bg-blue-500/20 text-blue-500' :
                health_label === 'Fair' ? 'bg-amber-500/20 text-amber-500' : 'bg-red-500/20 text-red-500'
            }`}>
            {health_label} Health
          </span>
          <span className="text-gray-500 text-xs font-medium">Verified by TrackSpendAI AI</span>
        </div>
        <h2 className="text-4xl font-bold mb-8 leading-tight max-w-2xl">{headline}</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {(top_insights || []).map((insight, i) => (
            <div key={i} className="flex gap-4 items-start">
              <div className="w-2 h-2 rounded-full bg-accent mt-2 shrink-0"></div>
              <p className="text-lg text-gray-300 leading-relaxed">{insight}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {/* Recommendations / Action Plan */}
        <div className="space-y-6">
          <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
            Action Plan
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {(recommendations || []).map((rec, i) => (
              <RecommendationCard key={i} rec={rec} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}


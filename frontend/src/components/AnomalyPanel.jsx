import React from 'react';
import { AlertTriangle, Info, CheckCircle } from 'lucide-react';

export default function AnomalyPanel({ report }) {
  const { anomalies, anomaly_narrative } = report;

  if (!anomalies || anomalies.length === 0) return null;

  return (
    <div className="bg-card border border-border overflow-hidden rounded-3xl shadow-xl mt-8">
      <div className="bg-amber-500/10 p-6 flex items-center gap-4 border-b border-border">
        <div className="p-3 bg-amber-500/20 rounded-2xl">
          <AlertTriangle className="w-6 h-6 text-amber-500" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Unusual spending detected</h2>
          <p className="text-amber-500/80 text-sm font-medium">{anomalies.length} potential patterns worth checking</p>
        </div>
      </div>
      
      <div className="p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {(anomalies || []).map((anomaly, i) => (
            <div key={i} className="bg-background/50 border border-border p-6 rounded-2xl relative group">
              <div className="flex justify-between items-start mb-4">
                <span className={`text-[10px] uppercase tracking-widest font-bold px-2 py-1 rounded-md ${
                  anomaly.severity === 'high' ? 'bg-red-500/20 text-red-500' :
                  anomaly.severity === 'medium' ? 'bg-amber-500/20 text-amber-500' : 'bg-blue-500/20 text-blue-500'
                }`}>
                  {anomaly.severity || 'low'} Priority
                </span>
                <span className="text-lg font-bold">₹{(anomaly.amount || 0).toLocaleString('en-IN')}</span>
              </div>
              <h4 className="font-bold text-lg mb-1">{anomaly.type || 'Unusual Pattern'}</h4>
              <p className="text-gray-400 text-sm mb-4 leading-relaxed">{anomaly.reason || 'Detected unusal activity.'}</p>
              <div className="flex items-center justify-between text-[11px] text-gray-500">
                <span>{anomaly.date ? new Date(anomaly.date).toLocaleDateString() : 'Recent'}</span>
                <button className="opacity-0 group-hover:opacity-100 transition-opacity text-accent hover:underline">Mark as safe</button>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-background border border-border p-6 rounded-2xl flex gap-4 items-start">
             <div className="p-2 bg-accent/10 rounded-lg">
                <Info className="w-5 h-5 text-accent" />
             </div>
             <p className="text-gray-300 italic leading-relaxed">
                "{anomaly_narrative}"
             </p>
        </div>
      </div>
    </div>
  );
}

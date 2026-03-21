import React, { useState, useEffect } from 'react';
import { pingServer, streamAnalysis } from './services/api';
import UploadZone from './components/UploadZone';
import PipelineProgress from './components/PipelineProgress';
import SpendingDashboard from './components/SpendingDashboard';
import AnomalyPanel from './components/AnomalyPanel';
import InsightsPanel from './components/InsightsPanel';
import TransactionTable from './components/TransactionTable';
import { Search, User, BarChart3, Shield, Info, Sun, Moon } from 'lucide-react';

export default function App() {
  const [isWaking, setIsWaking] = useState(true);
  const [pipelineState, setPipelineState] = useState('idle'); // idle, running, result, error
  const [progress, setProgress] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [isDark, setIsDark] = useState(true);
  const [isConnected, setIsConnected] = useState(true);

  // ... (useEffect and handlers same as before)
  useEffect(() => {
    const wake = async () => {
      const ready = await pingServer();
      setIsConnected(ready);
      setIsWaking(false);
    };
    wake();
  }, []);

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
    }
  }, [isDark]);

  const handleUpload = async (file, password = '') => {
    setPipelineState('running');
    setProgress({ step: 1, message: 'Attaching file...', status: 'running' });
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    if (password) formData.append('password', password);

    streamAnalysis(formData,
      (prog) => setProgress(prog),
      (res) => {
        setResult(res.report);
        setPipelineState('result');
      },
      (err) => {
        setError(err.message || 'Analysis failed. Please try again.');
        setPipelineState('idle');
      }
    );
  };

  const handleDemo = async () => {
    const response = await fetch('/demo_transactions.csv');
    const blob = await response.blob();
    const file = new File([blob], 'demo_transactions.csv', { type: 'text/csv' });
    handleUpload(file);
  };

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Privacy Modal */}
      {showPrivacy && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 backdrop-blur-sm bg-black/40 animate-in fade-in duration-300">
          <div className="bg-card border border-border p-8 rounded-3xl max-w-lg w-full shadow-2xl">
            <h3 className="text-2xl font-bold mb-4 flex items-center gap-3">
              <Shield className="text-accent w-6 h-6" /> Security & Privacy
            </h3>
            <ul className="space-y-4 text-gray-400 text-sm">
              <li className="flex gap-3">
                <span className="text-accent font-bold">•</span>
                <span><b>Local Filtering:</b> Your transaction descriptions are parsed locally. Only anonymized metadata is processed by AI.</span>
              </li>
              <li className="flex gap-3">
                <span className="text-accent font-bold">•</span>
                <span><b>No Storage:</b> TrackSpendAI does not save your financial data. Once you refresh, the analysis is cleared.</span>
              </li>
              <li className="flex gap-3">
                <span className="text-accent font-bold">•</span>
                <span><b>Bank-Grade Parsing:</b> We use standard ETL pipelines to ensure your PDF/CSV data is handled safely.</span>
              </li>
            </ul>
            <button
              onClick={() => setShowPrivacy(false)}
              className="mt-8 w-full bg-accent text-[#ffffff] py-3 rounded-2xl font-bold hover:brightness-110 transition-all"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Header */}
      <nav className="border-b border-border bg-background/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setPipelineState('idle')}>
            <div className="w-10 h-10 bg-accent rounded-xl flex items-center justify-center shadow-lg shadow-accent/20">
              <BarChart3 className="text-[#ffffff] w-6 h-6" />
            </div>
            <span className="text-2xl font-black tracking-tighter">TrackSpendAI</span>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsDark(!isDark)}
              className="flex items-center justify-center w-10 h-10 bg-card border border-border rounded-xl text-gray-400 hover:text-accent transition-all"
              title="Toggle Theme"
            >
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <button
              onClick={() => setShowPrivacy(true)}
              className="flex items-center gap-2 px-4 py-2 bg-card border border-border rounded-xl text-xs font-bold text-accent hover:bg-border transition-all"
            >
              <Shield className="w-4 h-4" /> Privacy Report
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 pt-16">
        {pipelineState === 'idle' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <div className="text-center mb-16">
              <h1 className="text-6xl font-black mb-6 tracking-tight leading-tight">
                Intelligence for your <span className="text-accent">UPI spending.</span>
              </h1>
              <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                Upload your digital statement and watch our AI agents uncover hidden spending patterns, detected anomalies, and grounded financial advice.
              </p>
            </div>
            <UploadZone onUpload={handleUpload} onDemo={handleDemo} isWaking={isWaking} />

            {error && (
              <div className="mt-8 max-w-xl mx-auto p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-4 text-red-500">
                <Info className="w-5 h-5 shrink-0" />
                <p className="text-sm font-medium">{error}</p>
              </div>
            )}

            {!isConnected && !isWaking && (
              <div className="mt-8 max-w-xl mx-auto p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex items-center gap-4 text-amber-500 text-left">
                <Info className="w-6 h-6 shrink-0" />
                <p className="text-sm font-medium">Warning: Handshake failed. Could not reach the backend server. If you just deployed, check if the server is still booting up or verify your API URL.</p>
              </div>
            )}
          </div>
        )}

        {pipelineState === 'running' && (
          <PipelineProgress progress={progress} />
        )}

        {pipelineState === 'result' && result && (
          <div className="animate-in fade-in duration-1000">
            <div className="flex items-center justify-between mb-12">
              <div>
                <h2 className="text-3xl font-bold">Analysis Results</h2>
                <p className="text-gray-400">For educational purposes only. Consult a SEBI-registered financial advisor for personalised advice.</p>
              </div>
              <button
                onClick={() => setPipelineState('idle')}
                className="bg-card hover:bg-border text-white px-6 py-3 rounded-2xl font-bold text-sm transition-all border border-border"
              >
                Analyze New
              </button>
            </div>
            <SpendingDashboard report={result} />
            <AnomalyPanel report={result} />
            <InsightsPanel report={result} />
            <TransactionTable transactions={result.transactions} />
          </div>
        )}
      </main>

      <footer className="mt-20 py-12 border-t border-border bg-card/10 text-center">
        <p className="text-xs text-gray-600 font-medium">© 2024 TrackSpendAI · AI-POWERED UPI INTELLIGENCE PLATFORM</p>
      </footer>
    </div>
  );
}

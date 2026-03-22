import React, { useState, useRef } from 'react';
import { Upload, FileText, ArrowRight, Lock } from 'lucide-react';

export default function UploadZone({ onUpload, onDemo, isWaking }) {
  const [dragActive, setDragActive] = useState(false);
  const [needsPassword, setNeedsPassword] = useState(false);
  const [password, setPassword] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (file) => {
    setSelectedFile(file);
    onUpload(file);
  };

  if (needsPassword) {
    return (
      <div className="max-w-xl mx-auto p-12 bg-card border border-border rounded-3xl text-center shadow-2xl">
        <div className="w-16 h-16 bg-accent/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <Lock className="w-8 h-8 text-accent" />
        </div>
        <h2 className="text-2xl font-bold mb-2">Password Protected</h2>
        <p className="text-muted-foreground mb-8">
          This PDF is protected. For PhonePe statements, enter your 10-digit mobile number.
        </p>
        <div className="flex gap-2">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter password"
            className="flex-1 bg-background border border-border rounded-xl px-4 py-3 focus:outline-none focus:border-accent"
          />
          <button
            onClick={() => onUpload(selectedFile, password)}
            className="bg-accent text-[#ffffff] hover:bg-accent/80 px-6 py-3 rounded-xl font-semibold transition-all"
          >
            Unlock
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div
        className={`relative p-12 border-2 border-dashed rounded-3xl text-center transition-all ${
          dragActive ? 'border-accent bg-accent/5' : 'border-border bg-card'
        }`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}
          accept=".pdf,.csv,.xlsx"
        />
        
        <div className="w-20 h-20 bg-accent/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <Upload className="w-10 h-10 text-accent" />
        </div>
        
        <h2 className="text-3xl font-bold mb-4">Upload your UPI statement</h2>
        <p className="text-muted-foreground mb-8 text-lg">
          Drag and drop your PDF, CSV, or XLSX statement here.<br />
          Works with PhonePe, Paytm, and all major banks.
        </p>
        
        <button
          onClick={() => inputRef.current.click()}
          className="bg-accent hover:bg-accent/80 text-[#ffffff] px-8 py-4 rounded-2xl font-bold text-lg transition-all shadow-lg shadow-accent/20 flex items-center gap-2 mx-auto"
        >
          Select File <ArrowRight className="w-5 h-5" />
        </button>

        <p className="mt-6 text-sm text-subtle flex items-center justify-center gap-2">
            <Lock className="w-4 h-4" /> Your data never leaves this session and is not stored.
        </p>
      </div>

      <div className="mt-8 text-center">
        <button
          onClick={onDemo}
          className="text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2 mx-auto group"
        >
          Try with demo data <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>

    </div>
  );
}

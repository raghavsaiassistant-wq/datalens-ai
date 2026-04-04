import React from 'react';
import { useAnalysis } from './hooks/useAnalysis';
import FileUpload from './components/FileUpload';
import AnalysisProgress from './components/AnalysisProgress';
import Dashboard from './components/Dashboard';
import SummaryPanel from './components/SummaryPanel';
import FindingsCard from './components/FindingsCard';
import AnomalyAlert from './components/AnomalyAlert';
import NextSteps from './components/NextSteps';
import QAPanel from './components/QAPanel';
import { RefreshCcw, AlertCircle, Linkedin, ExternalLink } from 'lucide-react';

function App() {
  const {
    uploadFile, askQuestion, resetAnalysis,
    analysisResult, isLoading, loadingStep, progress, error, uploadStartTime
  } = useAnalysis();

  return (
    <div className="min-h-screen bg-[#060810] selection:bg-accent/30 selection:text-white text-white overflow-x-hidden relative">

      {/* ── Cinematic background ── */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[45%] h-[45%] bg-accent/[0.05] rounded-full blur-[130px]" />
        <div className="absolute top-[20%] right-[-5%] w-[35%] h-[35%] bg-accent-blue/[0.04] rounded-full blur-[110px]" />
        <div className="absolute bottom-[10%] left-[30%] w-[30%] h-[30%] bg-[#7C3AED]/[0.03] rounded-full blur-[100px]" />
      </div>

      {/* ── Global Error Banner ── */}
      {error && !isLoading && (
        <div className="fixed top-6 left-1/2 -translate-x-1/2 z-[100] animate-in slide-in-from-top-4 max-w-lg w-full px-4">
          <div className="bg-[#1a0808] border border-red-500/30 backdrop-blur-xl text-white px-6 py-4 rounded-2xl shadow-2xl flex items-start gap-4 ring-1 ring-red-500/10">
            <AlertCircle className="shrink-0 mt-0.5 text-red-400" size={18} />
            <div className="flex-grow">
              <p className="text-sm font-mono text-red-300/90 leading-relaxed">{error}</p>
            </div>
            <button
              onClick={resetAnalysis}
              className="text-white/30 hover:text-white shrink-0 p-1 transition-colors font-mono text-sm"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* ── Main State Machine ── */}
      <main className="relative z-10 w-full">
        {!analysisResult && !isLoading ? (
          <FileUpload onUpload={uploadFile} />

        ) : isLoading ? (
          <AnalysisProgress progress={progress} message={loadingStep} startTime={uploadStartTime} />

        ) : analysisResult ? (
          <div className="max-w-[1700px] mx-auto px-5 md:px-10 xl:px-16 py-8 animate-in fade-in duration-700 w-full">

            {/* ── Dashboard Header ── */}
            <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-12 gap-6 pb-8 border-b border-white/[0.06]">
              <div className="flex items-start gap-4">
                {/* Logo mark */}
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-accent to-[#4a7a00] flex items-center justify-center shadow-[0_0_20px_rgba(118,185,0,0.3)] shrink-0 mt-0.5">
                  <span className="font-serif italic text-white text-xl font-bold leading-none">L</span>
                </div>
                <div>
                  <h1 className="text-2xl md:text-3xl font-serif italic text-white tracking-tight">
                    DataLens <span className="text-white/30">AI Intelligence</span>
                  </h1>
                  <div className="flex flex-wrap items-center gap-4 mt-1.5 text-[10px] font-mono text-white/30 uppercase tracking-[0.18em]">
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
                      <span>Synthesis Active</span>
                    </div>
                    <span className="w-1 h-1 bg-white/10 rounded-full" />
                    <span>Llama 3.3 70B</span>
                    <span className="w-1 h-1 bg-white/10 rounded-full" />
                    <span>{analysisResult.processing_time?.toFixed(1)}s</span>
                    <span className="w-1 h-1 bg-white/10 rounded-full" />
                    <span>{analysisResult.profile?.rows?.toLocaleString()} rows</span>
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <a
                  href="https://www.linkedin.com/in/raghav-modi-a94b60228"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#0A66C2]/10 border border-[#0A66C2]/20 hover:bg-[#0A66C2]/20 transition-all text-[11px] font-mono text-[#0A66C2]/70 hover:text-[#0A66C2] group"
                >
                  <Linkedin size={12} />
                  <span>Raghav Modi</span>
                  <ExternalLink size={10} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                </a>
                <button
                  onClick={() => window.print()}
                  className="flex items-center gap-2 px-4 py-2.5 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] hover:border-white/20 rounded-xl text-[11px] font-mono font-bold uppercase tracking-widest transition-all"
                >
                  Export PDF
                </button>
                <button
                  onClick={resetAnalysis}
                  className="flex items-center gap-2 px-5 py-2.5 bg-accent text-[#060810] rounded-xl text-[11px] font-mono font-bold uppercase tracking-widest transition-all hover:bg-white hover:shadow-[0_0_25px_rgba(118,185,0,0.3)] active:scale-95"
                >
                  <RefreshCcw size={13} />
                  New Analysis
                </button>
              </div>
            </header>

            {/* ── Dashboard Content ── */}
            <div className="space-y-10 mb-28">
              {/* Anomaly alerts */}
              <AnomalyAlert anomalies={analysisResult.anomalies} />

              {/* Summary + Findings */}
              <div className="grid grid-cols-1 xl:grid-cols-[1.1fr_1fr] gap-8">
                <SummaryPanel
                  summary={analysisResult.executive_summary}
                  healthScore={analysisResult.data_health_score}
                  profile={analysisResult.profile}
                />
                <FindingsCard findings={analysisResult.key_findings} />
              </div>

              {/* Charts */}
              <Dashboard charts={analysisResult.charts} />

              {/* Next steps */}
              <NextSteps steps={analysisResult.next_steps} />
            </div>

            {/* Q&A panel */}
            <QAPanel onAskQuestion={askQuestion} disabled={false} />

            {/* ── Footer ── */}
            <footer className="pt-12 pb-10 border-t border-white/[0.05] flex flex-col md:flex-row justify-between items-center gap-4">
              <p className="text-[9px] font-mono uppercase tracking-[0.4em] text-white/15">
                DataLens AI · Neural Data Model v1.0 · © 2026 DataLens Labs
              </p>
              <a
                href="https://www.linkedin.com/in/raghav-modi-a94b60228"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 group"
              >
                <span className="text-[9px] font-mono uppercase tracking-[0.3em] text-white/15 group-hover:text-white/40 transition-colors">
                  Created by
                </span>
                <span className="text-[9px] font-mono uppercase tracking-[0.3em] text-accent/40 group-hover:text-accent transition-colors font-bold">
                  Raghav Modi
                </span>
                <Linkedin size={11} className="text-[#0A66C2]/30 group-hover:text-[#0A66C2] transition-colors" />
              </a>
            </footer>
          </div>
        ) : null}
      </main>
    </div>
  );
}

export default App;

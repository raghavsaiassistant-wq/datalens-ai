import React, { useEffect } from 'react';
import { useAnalysis } from './hooks/useAnalysis';
import FileUpload from './components/FileUpload';
import AnalysisProgress from './components/AnalysisProgress';
import SummaryPanel from './components/SummaryPanel';
import FindingsCard from './components/FindingsCard';
import AnomalyAlert from './components/AnomalyAlert';
import NextSteps from './components/NextSteps';
import QAPanel from './components/QAPanel';
import SmartDashboard from './components/SmartDashboard';
import { DataStoreProvider, useDataStore } from './store/dataStore.jsx';
import { useFilteredInsights } from './hooks/useFilteredInsights';
import { RefreshCcw, AlertCircle, Linkedin, ExternalLink } from 'lucide-react';

// ─── Inner app — has access to both useAnalysis and useDataStore ──────── //
function AppInner() {
  const {
    uploadFile, askQuestion, resetAnalysis,
    analysisResult, isLoading, loadingStep, progress, error, sessionId, uploadStartTime
  } = useAnalysis();

  const { dispatch } = useDataStore();

  // Sync analysisResult into DataStore whenever it arrives
  useEffect(() => {
    if (analysisResult) {
      dispatch({ type: 'SET_RAW_DATA', payload: analysisResult });
    } else {
      dispatch({ type: 'RESET' });
    }
  }, [analysisResult, dispatch]);

  // Hook up insight regeneration lifecycle
  useFilteredInsights(sessionId);

  return (
    <div className="min-h-screen bg-[#F5F5F7] selection:bg-accent/20 selection:text-[#1D1D1F] text-[#1D1D1F] overflow-x-hidden">

      {/* ── Global Error Banner ── */}
      {error && !isLoading && (
        <div className="fixed top-6 left-1/2 -translate-x-1/2 z-[100] animate-in slide-in-from-top-4 max-w-lg w-full px-4">
          <div className="bg-white border border-red-200 text-[#1D1D1F] px-6 py-4 rounded-2xl shadow-[0_8px_40px_rgba(0,0,0,0.12)] flex items-start gap-4">
            <AlertCircle className="shrink-0 mt-0.5 text-red-500" size={18} />
            <div className="flex-grow">
              <p className="text-sm font-mono text-red-600 leading-relaxed">{error}</p>
            </div>
            <button
              onClick={resetAnalysis}
              className="text-[#8E8E93] hover:text-[#1D1D1F] shrink-0 p-1 transition-colors font-mono text-sm"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* ── Main State Machine ── */}
      <main className="w-full">
        {!analysisResult && !isLoading ? (
          <FileUpload onUpload={uploadFile} />

        ) : isLoading ? (
          <AnalysisProgress progress={progress} message={loadingStep} startTime={uploadStartTime} />

        ) : analysisResult ? (
          <div className="max-w-[1700px] mx-auto px-5 md:px-10 xl:px-16 py-8 animate-in fade-in duration-700 w-full">

            {/* ── Dashboard Header ── */}
            <header className="bg-white rounded-2xl border border-black/[0.07] shadow-[0_2px_12px_rgba(0,0,0,0.06)] px-7 py-5 flex flex-col lg:flex-row justify-between items-start lg:items-center mb-8 gap-5">
              <div className="flex items-start gap-4">
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-accent to-[#4a7a00] flex items-center justify-center shadow-[0_2px_10px_rgba(118,185,0,0.25)] shrink-0 mt-0.5">
                  <span className="font-serif italic text-white text-xl font-bold leading-none">L</span>
                </div>
                <div>
                  <h1 className="text-2xl md:text-3xl font-serif italic text-[#1D1D1F] tracking-tight">
                    DataLens <span className="text-[#8E8E93]">AI Intelligence</span>
                  </h1>
                  <div className="flex flex-wrap items-center gap-4 mt-1.5 text-[10px] font-mono text-[#8E8E93] uppercase tracking-[0.18em]">
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
                      <span>Synthesis Active</span>
                    </div>
                    <span className="w-1 h-1 bg-black/10 rounded-full" />
                    <span>Llama 3.3 70B</span>
                    <span className="w-1 h-1 bg-black/10 rounded-full" />
                    <span>{analysisResult.processing_time?.toFixed(1)}s</span>
                    <span className="w-1 h-1 bg-black/10 rounded-full" />
                    <span>{analysisResult.profile?.rows?.toLocaleString()} rows</span>
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <a
                  href="https://www.linkedin.com/in/raghav-modi-a94b60228"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#F5F5F7] border border-black/[0.08] hover:bg-[#0A66C2]/[0.06] hover:border-[#0A66C2]/30 transition-all text-[11px] font-mono text-[#6E6E73] hover:text-[#0A66C2] group"
                >
                  <Linkedin size={12} />
                  <span>Raghav Modi</span>
                  <ExternalLink size={10} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                </a>
                <button
                  onClick={() => window.print()}
                  className="flex items-center gap-2 px-4 py-2.5 bg-[#F5F5F7] hover:bg-[#E5E5EA] border border-black/[0.08] hover:border-black/[0.15] rounded-xl text-[11px] font-mono font-bold uppercase tracking-widest transition-all text-[#3A3A3C]"
                >
                  Export PDF
                </button>
                <button
                  onClick={resetAnalysis}
                  className="flex items-center gap-2 px-5 py-2.5 bg-[#1D1D1F] text-white rounded-xl text-[11px] font-mono font-bold uppercase tracking-widest transition-all hover:bg-[#3A3A3C] hover:shadow-[0_4px_16px_rgba(0,0,0,0.20)] active:scale-95"
                >
                  <RefreshCcw size={13} />
                  New Analysis
                </button>
              </div>
            </header>

            {/* ── Dashboard Content ── */}
            <div className="space-y-8 mb-28">
              {/* Anomaly alerts */}
              <AnomalyAlert anomalies={analysisResult.anomalies} />

              {/* Summary + Findings */}
              <div className="grid grid-cols-1 xl:grid-cols-[1.1fr_1fr] gap-6">
                <SummaryPanel
                  summary={analysisResult.executive_summary}
                  healthScore={analysisResult.data_health_score}
                  profile={analysisResult.profile}
                />
                <FindingsCard findings={analysisResult.key_findings} />
              </div>

              {/* Smart Dashboard: FilterBar + InsightsPanel + Charts */}
              <SmartDashboard charts={analysisResult.charts} />

              {/* Next steps */}
              <NextSteps steps={analysisResult.next_steps} />
            </div>

            {/* Q&A panel */}
            <QAPanel onAskQuestion={askQuestion} disabled={false} />

            {/* ── Footer ── */}
            <footer className="pt-10 pb-8 border-t border-black/[0.06] flex flex-col md:flex-row justify-between items-center gap-4">
              <p className="text-[9px] font-mono uppercase tracking-[0.4em] text-[#8E8E93]">
                DataLens AI · Neural Data Model v2.0 · © 2026 DataLens Labs
              </p>
              <a
                href="https://www.linkedin.com/in/raghav-modi-a94b60228"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 group"
              >
                <span className="text-[9px] font-mono uppercase tracking-[0.3em] text-[#8E8E93] group-hover:text-[#6E6E73] transition-colors">
                  Created by
                </span>
                <span className="text-[9px] font-mono uppercase tracking-[0.3em] text-[#1D1D1F] group-hover:text-accent transition-colors font-bold">
                  Raghav Modi
                </span>
                <Linkedin size={11} className="text-[#0A66C2]/50 group-hover:text-[#0A66C2] transition-colors" />
              </a>
            </footer>
          </div>
        ) : null}
      </main>
    </div>
  );
}

// ─── Root: wraps AppInner with DataStoreProvider ──────────────────────── //
function App() {
  return (
    <DataStoreProvider>
      <AppInner />
    </DataStoreProvider>
  );
}

export default App;

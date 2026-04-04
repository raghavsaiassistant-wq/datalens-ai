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
import { RefreshCcw, AlertCircle } from 'lucide-react';

function App() {
  const { uploadFile, askQuestion, resetAnalysis, analysisResult, isLoading, loadingStep, progress, error } = useAnalysis();

  return (
    <div className="min-h-screen bg-[#0A0C10] selection:bg-accent/30 selection:text-white font-sans text-white overflow-x-hidden relative">
      
      {/* Cinematic Background Glows */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-accent/5 rounded-full blur-[120px]"></div>
        <div className="absolute top-[20%] right-[-5%] w-[30%] h-[30%] bg-accent-blue/5 rounded-full blur-[100px]"></div>
      </div>

      {/* Global Error Banner */}
      {error && !isLoading && (
        <div className="fixed top-6 left-1/2 -translate-x-1/2 z-[100] animate-in slide-in-from-top-4 max-w-lg w-full px-4">
          <div className="bg-danger/90 backdrop-blur-xl text-white px-6 py-4 rounded-2xl shadow-2xl flex items-start gap-4 border border-white/10 ring-1 ring-danger/20">
            <AlertCircle className="shrink-0 mt-0.5" size={20} />
            <div className="flex-grow">
              <p className="text-sm font-medium leading-relaxed">{error}</p>
            </div>
            <button onClick={resetAnalysis} className="text-white/40 hover:text-white shrink-0 p-1 transition-colors">
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Main State Machine */}
      <main className="relative z-10 w-full">
        {!analysisResult && !isLoading ? (
          <FileUpload onUpload={uploadFile} />
        ) : isLoading ? (
          <AnalysisProgress progress={progress} message={loadingStep} />
        ) : analysisResult ? (
          <div className="max-w-[1600px] mx-auto p-6 md:p-12 animate-in fade-in duration-1000 w-full">
            
            {/* Header Section */}
            <header className="flex flex-col lg:flex-row justify-between items-start lg:items-end mb-16 gap-8 border-b border-white/5 pb-10">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center">
                    <span className="font-serif italic text-accent text-xl font-bold">L</span>
                  </div>
                  <h1 className="text-4xl font-serif text-white italic tracking-tight">
                    DataLens <span className="text-white/40">AI Intelligence</span>
                  </h1>
                </div>
                <div className="flex flex-wrap items-center gap-6 text-[10px] font-mono text-[#8E9AAF] uppercase tracking-[0.2em] font-bold">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse"></span>
                    <span>Synthesis Active</span>
                  </div>
                  <span className="w-1 h-1 bg-white/10 rounded-full"></span>
                  <span>Engine: Llama 3 70B</span>
                  <span className="w-1 h-1 bg-white/10 rounded-full"></span>
                  <span>Latency: {analysisResult.processing_time?.toFixed(1)}s</span>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-4">
                <button className="flex items-center gap-2 px-5 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-[11px] font-mono font-bold uppercase tracking-widest transition-all hover:border-white/20">
                  Share Report
                </button>
                <button 
                  onClick={resetAnalysis}
                  className="flex items-center gap-2 px-6 py-3 bg-accent text-[#0A0C10] rounded-xl text-[11px] font-mono font-bold uppercase tracking-widest transition-all hover:bg-white hover:shadow-[0_0_20px_rgba(118,185,0,0.3)] active:scale-95"
                >
                  <RefreshCcw size={14} className="group-hover:rotate-180 transition-transform duration-500" /> New Analysis
                </button>
              </div>
            </header>

            <section className="space-y-12 mb-20">
              <AnomalyAlert anomalies={analysisResult.anomalies} />

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                <SummaryPanel 
                  summary={analysisResult.executive_summary} 
                  healthScore={analysisResult.data_health_score}
                  profile={analysisResult.profile}
                />
                <FindingsCard findings={analysisResult.key_findings} />
              </div>

              <Dashboard charts={analysisResult.charts} />

              <NextSteps steps={analysisResult.next_steps} />
            </section>

            <QAPanel onAskQuestion={askQuestion} disabled={false} />
            
            <footer className="pt-20 pb-10 border-t border-white/5 flex justify-between items-center opacity-30 text-[9px] font-mono uppercase tracking-[0.4em]">
              <span>Neural Data Model v1.4.2</span>
              <span>© 2026 DataLens Labs</span>
            </footer>
          </div>
        ) : null}
      </main>
    </div>
  );
}

export default App;

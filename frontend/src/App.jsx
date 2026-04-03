import React from 'react';
import { useAnalysis } from './hooks/useAnalysis';
import FileUpload from './components/FileUpload';
import LoadingState from './components/LoadingState';
import Dashboard from './components/Dashboard';
import SummaryPanel from './components/SummaryPanel';
import FindingsCard from './components/FindingsCard';
import AnomalyAlert from './components/AnomalyAlert';
import NextSteps from './components/NextSteps';
import QAPanel from './components/QAPanel';
import { RefreshCcw, AlertCircle } from 'lucide-react';

function App() {
  const { uploadFile, askQuestion, resetAnalysis, analysisResult, isLoading, loadingStep, error } = useAnalysis();

  return (
    <div className="min-h-screen bg-primary selection:bg-accent/30 selection:text-white font-sans text-white overflow-x-hidden">
      
      {/* GLobal Error Banner */}
      {error && !isLoading && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-top-4 max-w-lg w-full">
          <div className="bg-danger/90 backdrop-blur-md text-white px-4 py-3 rounded-lg shadow-2xl flex items-start gap-3 border border-danger">
            <AlertCircle className="shrink-0 mt-0.5" size={20} />
            <div className="flex-grow">
              <p className="text-sm font-medium leading-relaxed">{error}</p>
            </div>
            <button onClick={resetAnalysis} className="text-white/70 hover:text-white shrink-0 p-1">
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Main State Machine */}
      {!analysisResult && !isLoading ? (
        <FileUpload onUpload={uploadFile} />
      ) : isLoading ? (
        <LoadingState step={loadingStep} />
      ) : analysisResult ? (
        <div className="max-w-[1600px] mx-auto p-4 md:p-8 animate-in fade-in duration-700 w-full">
          
          {/* Header */}
          <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4 border-b border-white/10 pb-6">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white mb-1">
                DataLens <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-accent-blue">AI Report</span>
              </h1>
              <p className="text-sm text-secondary flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-success animate-pulse"></span>
                Analysis complete • {analysisResult.processing_time?.toFixed(1)}s processing time
              </p>
            </div>
            <button 
              onClick={resetAnalysis}
              className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-medium transition-colors"
            >
              <RefreshCcw size={16} /> New Analysis
            </button>
          </header>

          <AnomalyAlert anomalies={analysisResult.anomalies} />

          <Dashboard charts={analysisResult.charts} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <SummaryPanel 
              summary={analysisResult.executive_summary} 
              healthScore={analysisResult.data_health_score}
              profile={analysisResult.profile}
            />
            <FindingsCard findings={analysisResult.key_findings} />
          </div>

          <NextSteps steps={analysisResult.next_steps} />

          <QAPanel onAskQuestion={askQuestion} disabled={false} />
          
        </div>
      ) : null}
      
    </div>
  );
}

export default App;

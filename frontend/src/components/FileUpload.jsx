import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Upload, FileText, Table2, FileJson, FileCode, ImageIcon,
  FileSpreadsheet, Sparkles, Brain, BarChart3, Zap, ShieldCheck,
  MessageSquare, ArrowRight, Linkedin, Globe, CheckCircle2, FileType
} from 'lucide-react';

const SUPPORTED_EXTS = ['.csv','.txt','.xls','.xlsx','.sql','.json','.pdf','.png','.jpg','.jpeg','.webp'];

const FORMAT_PILLS = [
  { ext: 'CSV / TXT', icon: Table2, color: '#76B900' },
  { ext: 'XLSX / XLS', icon: FileSpreadsheet, color: '#00E5FF' },
  { ext: 'JSON', icon: FileJson, color: '#A78BFA' },
  { ext: 'PDF', icon: FileText, color: '#FB923C' },
  { ext: 'SQL', icon: FileCode, color: '#F472B6' },
  { ext: 'PNG / JPG', icon: ImageIcon, color: '#34D399' },
];

const FEATURES = [
  { icon: Brain, label: 'Executive Summary', desc: 'Boardroom-ready paragraph with real numbers' },
  { icon: BarChart3, label: 'Auto Dashboard', desc: '7 chart types generated in seconds' },
  { icon: Zap, label: 'Anomaly Detection', desc: 'Statistical outliers flagged & explained' },
  { icon: MessageSquare, label: 'AI Q&A Chatbot', desc: 'Ask questions in plain English' },
  { icon: ShieldCheck, label: 'Health Score', desc: 'Data quality assessed 0–100' },
  { icon: Sparkles, label: 'Key Findings', desc: 'Top 3 insights with impact ratings' },
];

const FileUpload = ({ onUpload }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const getExt = (filename) => '.' + filename.split('.').pop().toLowerCase();

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setError(null);
    let file = acceptedFiles[0];
    if (!file && rejectedFiles.length > 0) file = rejectedFiles[0].file;
    if (!file) return;

    const ext = getExt(file.name);
    if (!SUPPORTED_EXTS.includes(ext)) {
      setError(`Unsupported format "${ext}". Accepted: CSV, XLSX, JSON, PDF, SQL, PNG, JPG`);
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setError('File exceeds 25 MB limit. Please upload a smaller file.');
      return;
    }
    setSelectedFile(file);
  }, []);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    onDragEnter: () => setIsDragOver(true),
    onDragLeave: () => setIsDragOver(false),
    maxFiles: 1,
  });

  const handleAnalyze = () => {
    if (selectedFile) onUpload(selectedFile);
  };

  return (
    <div className="min-h-screen bg-[#060810] flex flex-col relative overflow-hidden">

      {/* ── Ambient glows ── */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-accent/[0.06] rounded-full blur-[160px]" />
        <div className="absolute top-[30%] right-[-15%] w-[50%] h-[50%] bg-accent-blue/[0.05] rounded-full blur-[140px]" />
        <div className="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] bg-[#7C3AED]/[0.04] rounded-full blur-[120px]" />
        {/* Subtle grid */}
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
          }}
        />
      </div>

      {/* ── Navigation ── */}
      <nav className="relative z-10 flex items-center justify-between px-8 md:px-16 pt-8 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent to-[#4a7a00] flex items-center justify-center shadow-[0_0_20px_rgba(118,185,0,0.35)]">
            <span className="font-serif italic text-white text-lg font-bold leading-none">L</span>
          </div>
          <span className="font-serif italic text-white text-xl tracking-tight">
            DataLens <span className="text-white/25">AI</span>
          </span>
        </div>
        <div className="flex items-center gap-5">
          <span className="hidden md:flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-[0.2em] text-white/25">
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
            NVIDIA NIM Powered
          </span>
          <a
            href="https://www.linkedin.com/in/raghav-modi-a94b60228"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.07] hover:border-[#0A66C2]/40 hover:bg-[#0A66C2]/10 transition-all duration-300 group"
          >
            <Linkedin size={12} className="text-white/30 group-hover:text-[#0A66C2] transition-colors" />
            <span className="text-[10px] font-mono text-white/30 group-hover:text-white/70 transition-colors hidden sm:inline">
              Raghav Modi
            </span>
          </a>
        </div>
      </nav>

      {/* ── Hero ── */}
      <div className="relative z-10 flex-grow flex flex-col items-center justify-center px-6 md:px-12 py-10 max-w-5xl mx-auto w-full">

        {/* Badge */}
        <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-accent/[0.08] border border-accent/[0.18] mb-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <Sparkles size={12} className="text-accent" />
          <span className="text-[10px] font-mono uppercase tracking-[0.25em] text-accent font-bold">
            AI Data Intelligence Platform
          </span>
        </div>

        {/* Headline */}
        <h1 className="text-center text-4xl md:text-6xl lg:text-[5.5rem] font-serif italic text-white tracking-tight mb-5 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100 leading-[1.08]">
          Turn Raw Data Into
          <br />
          <span
            className="text-transparent bg-clip-text"
            style={{ backgroundImage: 'linear-gradient(135deg, #76B900 0%, #a0d400 40%, #00E5FF 100%)' }}
          >
            Executive Intelligence
          </span>
        </h1>

        <p className="text-center text-white/45 text-base md:text-lg font-light max-w-xl mb-10 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-150 leading-relaxed">
          Upload any file. Get an interactive AI dashboard with executive summary, anomaly
          detection, and natural language Q&amp;A — in under 30 seconds.
        </p>

        {/* ── Drop zone ── */}
        <div
          {...getRootProps()}
          className={`
            relative w-full max-w-xl rounded-3xl cursor-pointer
            border-2 transition-all duration-500 ease-out group
            animate-in fade-in zoom-in-95 duration-700 delay-200
            ${isDragOver
              ? 'border-accent bg-accent/[0.08] shadow-[0_0_60px_rgba(118,185,0,0.18)] scale-[1.02]'
              : selectedFile
                ? 'border-accent/40 bg-accent/[0.03] shadow-[0_0_30px_rgba(118,185,0,0.08)]'
                : 'border-white/[0.08] bg-white/[0.015] hover:border-accent/35 hover:bg-accent/[0.04] hover:shadow-[0_0_40px_rgba(118,185,0,0.08)]'
            }
          `}
        >
          <input {...getInputProps()} />

          <div className="relative z-10 flex flex-col items-center px-8 py-12 text-center">

            {/* Icon */}
            <div className={`
              w-20 h-20 rounded-3xl flex items-center justify-center mb-5 transition-all duration-500
              ${isDragOver
                ? 'bg-accent/15 border-2 border-accent shadow-[0_0_30px_rgba(118,185,0,0.25)] scale-110'
                : selectedFile
                  ? 'bg-accent/10 border border-accent/30'
                  : 'bg-white/[0.04] border border-white/[0.08] group-hover:bg-accent/8 group-hover:border-accent/20'
              }
            `}>
              {selectedFile
                ? <CheckCircle2 size={36} className="text-accent" />
                : isDragOver
                  ? <Sparkles size={36} className="text-accent animate-pulse" />
                  : <Upload size={36} className="text-white/30 group-hover:text-white/60 transition-colors" />
              }
            </div>

            {selectedFile ? (
              <>
                <p className="text-accent font-mono text-[11px] font-bold uppercase tracking-[0.25em] mb-1.5">
                  ✓ Ready for analysis
                </p>
                <p className="text-white text-lg font-medium mb-1 truncate max-w-[300px]">{selectedFile.name}</p>
                <p className="text-white/30 text-xs font-mono">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </>
            ) : isDragOver ? (
              <>
                <p className="text-accent text-xl font-serif italic mb-1">Drop to analyze</p>
                <p className="text-white/35 text-sm font-mono">Release to start AI processing</p>
              </>
            ) : (
              <>
                <p className="text-white text-xl font-serif italic mb-1.5">Drop your data file here</p>
                <p className="text-white/35 text-sm font-mono mb-7">
                  or <span className="text-accent underline underline-offset-2 cursor-pointer">browse files</span> · max 25 MB
                </p>
                {/* Format pills */}
                <div className="flex flex-wrap justify-center gap-2">
                  {FORMAT_PILLS.map(({ ext, icon: Icon, color }) => (
                    <div
                      key={ext}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.07] hover:border-white/20 transition-colors"
                    >
                      <Icon size={11} style={{ color }} />
                      <span className="text-[9px] font-mono font-bold text-white/40 uppercase tracking-widest">{ext}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-3 flex items-start gap-3 px-5 py-3 bg-red-500/[0.08] border border-red-500/25 rounded-2xl animate-in fade-in zoom-in-95 duration-300 max-w-xl w-full">
            <span className="text-red-400 shrink-0 mt-0.5">⚠</span>
            <span className="text-red-400 text-xs font-mono">{error}</span>
          </div>
        )}

        {/* Analyze Button */}
        <button
          onClick={handleAnalyze}
          disabled={!selectedFile}
          className={`
            mt-5 w-full max-w-xl py-4 rounded-2xl font-mono font-bold text-sm uppercase tracking-[0.25em]
            transition-all duration-500 relative overflow-hidden group/btn
            animate-in fade-in slide-in-from-bottom-4 duration-700 delay-250
            ${selectedFile
              ? 'bg-accent text-[#060810] hover:bg-white hover:shadow-[0_0_50px_rgba(118,185,0,0.35)] active:scale-[0.98] cursor-pointer'
              : 'bg-white/[0.04] text-white/20 cursor-not-allowed border border-white/[0.06]'
            }
          `}
        >
          {selectedFile && (
            <div className="absolute inset-0 bg-white/25 translate-x-[-110%] group-hover/btn:translate-x-[110%] transition-transform duration-700 ease-in-out skew-x-12" />
          )}
          <span className="relative z-10 flex items-center justify-center gap-2">
            {selectedFile ? (
              <>Begin AI Analysis <ArrowRight size={15} /></>
            ) : (
              'Upload a file to continue'
            )}
          </span>
        </button>

        {/* Security note */}
        <div className="mt-4 flex items-center gap-2 text-[10px] font-mono text-white/20 uppercase tracking-[0.2em] animate-in fade-in duration-700 delay-300">
          <FileType size={11} className="text-accent/40" />
          <span>Files deleted immediately after processing · No data stored</span>
        </div>

        {/* ── Features ── */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3.5 mt-14 w-full max-w-3xl animate-in fade-in slide-in-from-bottom-4 duration-700 delay-350">
          {FEATURES.map(({ icon: Icon, label, desc }, i) => (
            <div
              key={label}
              className="group/feat flex items-start gap-3 p-4 rounded-2xl bg-white/[0.015] border border-white/[0.05] hover:border-accent/25 hover:bg-accent/[0.04] transition-all duration-500 animate-in fade-in fill-mode-both"
              style={{ animationDelay: `${380 + i * 60}ms` }}
            >
              <div className="w-8 h-8 rounded-xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center shrink-0 group-hover/feat:bg-accent/10 group-hover/feat:border-accent/20 transition-all">
                <Icon size={14} className="text-white/35 group-hover/feat:text-accent transition-colors" />
              </div>
              <div>
                <p className="text-white/75 text-[11px] font-bold tracking-tight mb-0.5">{label}</p>
                <p className="text-white/25 text-[10px] font-light leading-relaxed">{desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Model pills */}
        <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 mt-10 animate-in fade-in duration-700 delay-500">
          {['Llama 3.3 70B', 'Kimi K2', 'MiniMax M2.5', 'Mistral 7B', 'Llama 3.1 8B', 'NV-EmbedQA', 'Qwen VL'].map((m, i) => (
            <span key={m} className="text-[9px] font-mono text-white/15 uppercase tracking-[0.2em]">
              {m}{i < 6 ? <span className="ml-5 text-white/[0.08]">·</span> : null}
            </span>
          ))}
        </div>
      </div>

      {/* ── Footer ── */}
      <footer className="relative z-10 border-t border-white/[0.04] px-8 md:px-16 py-5 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-white/20 text-[10px] font-mono uppercase tracking-[0.2em]">
          <Globe size={10} />
          <span>DataLens AI · v1.0 · Built on NVIDIA NIM Free APIs · Zero paid AI costs</span>
        </div>
        <a
          href="https://www.linkedin.com/in/raghav-modi-a94b60228"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 group/footer"
        >
          <span className="text-[10px] font-mono text-white/20 uppercase tracking-[0.15em]">Created by</span>
          <span className="text-[10px] font-mono font-bold text-accent/60 group-hover/footer:text-accent uppercase tracking-[0.15em] transition-colors">
            Raghav Modi
          </span>
          <Linkedin size={11} className="text-[#0A66C2]/50 group-hover/footer:text-[#0A66C2] transition-colors" />
        </a>
      </footer>
    </div>
  );
};

export default FileUpload;

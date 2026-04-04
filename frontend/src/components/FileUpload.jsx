import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileType, CheckCircle2, Binary, Database, Table, FileJson, FilePlus } from 'lucide-react';

const FileUpload = ({ onUpload }) => {
  const [selectedFile, setSelectedFile] = useState(null);

  const onDrop = useCallback(acceptedFiles => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/sql': ['.sql'],
      'application/json': ['.json'],
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/webp': ['.webp']
    },
    maxSize: 25 * 1024 * 1024 // 25MB
  });

  const handleAnalyze = () => {
    if (selectedFile) onUpload(selectedFile);
  };

  const formats = [
    { name: 'CSV', icon: Table },
    { name: 'Excel', icon: Database },
    { name: 'SQL', icon: Binary },
    { name: 'JSON', icon: FileJson },
    { name: 'PDF', icon: FilePlus },
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden bg-[#0A0C10]">
      {/* Dynamic Background Glows */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-accent/5 rounded-full blur-[150px] pointer-events-none animate-pulse"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-accent-blue/5 rounded-full blur-[150px] pointer-events-none animate-pulse delay-1000"></div>

      <div className="max-w-3xl w-full text-center relative z-10 mb-16 animate-in fade-in slide-in-from-bottom-8 duration-1000">
        <h1 className="text-7xl font-serif text-white mb-6 italic tracking-tight">
          DataLens <span className="text-accent">AI</span>
        </h1>
        <p className="text-xl text-[#8E9AAF] font-mono uppercase tracking-[0.4em] text-[12px] font-bold">
          Autonomous Data Intelligence Platform
        </p>
      </div>

      <div className="max-w-xl w-full relative z-10 animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-200">
        <div 
          {...getRootProps()} 
          className={`glass-card p-12 flex flex-col items-center justify-center cursor-pointer transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] border-2 border-dashed
            ${isDragActive ? 'border-accent bg-accent/5 scale-[1.03] shadow-[0_0_50px_rgba(118,185,0,0.1)]' : 'border-white/10 hover:border-white/30 hover:bg-white/[0.04]'}
            ${selectedFile ? 'border-accent/40 bg-accent/[0.02] shadow-[0_0_30px_rgba(118,185,0,0.05)]' : ''}
          `}
        >
          <input {...getInputProps()} />
          
          {selectedFile ? (
            <div className="text-center animate-in zoom-in-95 duration-500">
              <div className="w-24 h-24 bg-accent/10 rounded-3xl flex items-center justify-center mx-auto mb-6 border border-accent/20 shadow-[0_0_30px_rgba(118,185,0,0.15)]">
                <CheckCircle2 className="text-accent" size={48} />
              </div>
              <h3 className="text-2xl font-serif italic text-white mb-2 truncate max-w-sm mx-auto">
                {selectedFile.name}
              </h3>
              <p className="text-sm font-mono text-[#8E9AAF] uppercase tracking-widest">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • READY FOR SYNTHESIS
              </p>
            </div>
          ) : (
            <div className="text-center group">
              <div className="w-24 h-24 bg-white/[0.03] rounded-3xl flex items-center justify-center mx-auto mb-8 border border-white/10 group-hover:border-accent/40 group-hover:bg-accent/5 transition-all duration-500">
                <UploadCloud className={`text-white/30 transition-all duration-500 group-hover:text-accent group-hover:scale-110 ${isDragActive ? 'text-accent animate-bounce' : ''}`} size={48} />
              </div>
              <h3 className="text-2xl font-serif text-white mb-3 italic">
                {isDragActive ? "Infiltrating records..." : "Drop data source"}
              </h3>
              <p className="text-sm text-[#8E9AAF] font-serif italic mb-10 opacity-70">or click to browse local environment</p>
              
              <div className="flex flex-wrap justify-center gap-3 mt-4">
                {formats.map(({ name, icon: Icon }) => (
                  <div key={name} className="flex items-center gap-1.5 px-3 py-1.5 bg-white/[0.02] border border-white/5 rounded-lg text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest transition-colors hover:text-white/80 hover:border-white/20">
                    <Icon size={12} />
                    {name}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="mt-12 flex flex-col items-center">
          <button
            onClick={handleAnalyze}
            disabled={!selectedFile}
            className={`w-full py-5 px-10 rounded-2xl font-mono font-bold text-sm uppercase tracking-[0.3em] transition-all duration-500 shadow-2xl relative overflow-hidden group
              ${selectedFile 
                ? 'bg-accent text-[#0A0C10] hover:bg-white hover:shadow-[0_0_40px_rgba(118,185,0,0.4)] active:scale-95' 
                : 'bg-white/5 text-white/20 cursor-not-allowed border border-white/5'
              }
            `}
          >
            <span className="relative z-10">{selectedFile ? 'Begin Analysis' : 'Initialization required'}</span>
            {selectedFile && <div className="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 ease-in-out"></div>}
          </button>
          
          <div className="mt-6 flex items-center gap-2 text-[10px] font-mono text-[#8E9AAF] uppercase tracking-widest opacity-60">
            <FileType size={12} className="text-accent" />
            <span>Secure Upload • 25MB Limit</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;

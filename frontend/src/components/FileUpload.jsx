import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileType, CheckCircle2 } from 'lucide-react';

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

  const formats = ['.csv', '.xlsx', '.sql', '.json', '.pdf', '.png'];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-accent/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-accent-blue/10 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="max-w-2xl w-full text-center relative z-10 mb-10">
        <h1 className="text-5xl font-extrabold text-white mb-4 tracking-tight">
          DataLens <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-accent-blue">AI</span>
        </h1>
        <p className="text-xl text-secondary font-light">Upload any data file. Get AI insights instantly.</p>
      </div>

      <div className="max-w-xl w-full">
        <div 
          {...getRootProps()} 
          className={`glass-card p-10 flex flex-col items-center justify-center cursor-pointer transition-all duration-300 ease-out border-2 border-dashed
            ${isDragActive ? 'border-accent bg-accent/5 scale-[1.02]' : 'border-white/20 hover:border-white/40 hover:bg-white/[0.02]'}
            ${selectedFile ? 'border-accent/50 bg-accent/[0.02]' : ''}
          `}
        >
          <input {...getInputProps()} />
          
          {selectedFile ? (
            <div className="text-center animate-in fade-in zoom-in duration-300">
              <div className="w-20 h-20 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-success/20">
                <CheckCircle2 className="text-success" size={40} />
              </div>
              <h3 className="text-xl font-semibold text-white mb-1 truncate max-w-sm mx-auto">
                {selectedFile.name}
              </h3>
              <p className="text-sm text-secondary">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready to analyze
              </p>
            </div>
          ) : (
            <div className="text-center">
              <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-6 border border-white/10 group-hover:bg-white/10 transition-colors">
                <UploadCloud className={`text-white/50 ${isDragActive ? 'text-accent animate-bounce' : ''}`} size={40} />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                {isDragActive ? "Drop file here..." : "Drag & drop your file"}
              </h3>
              <p className="text-sm text-secondary mb-6">or click to browse from your computer</p>
              
              <div className="flex flex-wrap justify-center gap-2 mt-4">
                {formats.map(f => (
                  <span key={f} className="px-3 py-1 bg-white/5 border border-white/10 rounded-full text-xs font-medium text-white/70">
                    {f}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="mt-8 flex flex-col items-center">
          <button
            onClick={handleAnalyze}
            disabled={!selectedFile}
            className={`w-full py-4 px-8 rounded-xl font-bold text-lg transition-all duration-300 shadow-lg
              ${selectedFile 
                ? 'bg-gradient-to-r from-accent to-[rgba(118,185,0,0.8)] text-white hover:shadow-[0_0_30px_rgba(118,185,0,0.3)] hover:-translate-y-1' 
                : 'bg-white/10 text-white/40 cursor-not-allowed border border-white/5'
              }
            `}
          >
            {selectedFile ? 'Analyze Data' : 'Select a file to begin'}
          </button>
          <p className="text-xs text-secondary mt-4 font-medium flex items-center gap-1">
            <FileType size={14}/> Max file size: 25MB
          </p>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;

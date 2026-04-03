import React, { useState } from 'react';
import { getSeverityColor } from '../utils/chartHelpers';
import { TriangleAlert, X } from 'lucide-react';

const AnomalyAlert = ({ anomalies }) => {
  const [flags, setFlags] = useState(anomalies || []);
  const [isOpen, setIsOpen] = useState(true);

  if (!flags || flags.length === 0) return null;

  const dismiss = (index) => {
    setFlags(flags.filter((_, i) => i !== index));
    if (flags.length === 1) setIsOpen(false);
  };

  if (!isOpen) return null;

  return (
    <div className="mb-8">
      <div 
        className="flex items-center gap-2 mb-4 cursor-pointer"
        onClick={() => setIsOpen(!isOpen)}
      >
        <TriangleAlert className="text-warning" size={24} />
        <h2 className="text-xl font-semibold text-white">Data Anomalies</h2>
        <span className="bg-white/10 text-white px-2 py-0.5 rounded-full text-xs font-bold">
          {flags.length} Detected
        </span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {flags.map((flag, i) => (
          <div 
            key={i}
            className="glass-card p-4 relative flex items-start gap-4 border-l-4"
            style={{ borderLeftColor: getSeverityColor(flag.severity) }}
          >
            <button 
              onClick={() => dismiss(i)}
              className="absolute top-2 right-2 text-secondary hover:text-white transition-colors"
            >
              <X size={16} />
            </button>
            <div className="flex-grow">
              <div className="flex gap-2 mb-2 items-center text-xs font-semibold uppercase tracking-wider">
                <span className="bg-white/10 px-2 py-1 rounded text-white">{flag.column}</span>
                <span style={{ color: getSeverityColor(flag.severity) }}>{flag.anomaly_type.replace('_', ' ')}</span>
              </div>
              <p className="text-sm text-secondary leading-relaxed">{flag.explanation}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AnomalyAlert;

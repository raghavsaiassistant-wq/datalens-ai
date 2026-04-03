import React from 'react';
import { getImpactColor } from '../utils/chartHelpers';
import { Lightbulb } from 'lucide-react';

const FindingsCard = ({ findings }) => {
  if (!findings || findings.length === 0) return null;

  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-6">
        <Lightbulb className="text-accent" size={24} />
        <h2 className="text-xl font-semibold text-white">Key Findings</h2>
      </div>
      <div className="flex flex-col gap-4 flex-grow">
        {findings.map((finding, i) => (
          <div 
            key={i} 
            className="p-4 rounded-lg bg-white/5 border-l-4"
            style={{ borderLeftColor: getImpactColor(finding.impact) }}
          >
            <div className="flex justify-between items-start mb-1">
              <h3 className="font-semibold text-white text-md">{finding.headline}</h3>
              <span className="text-xs px-2 py-1 rounded-full bg-white/10 uppercase tracking-wider font-semibold" style={{ color: getImpactColor(finding.impact) }}>
                {finding.impact}
              </span>
            </div>
            <p className="text-sm text-secondary leading-relaxed">{finding.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FindingsCard;

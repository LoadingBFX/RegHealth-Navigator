import React, { useState } from 'react';
import { UniqueSectionAnalysis } from '../../services/api';
import { ChevronDown, ChevronUp, FileText, AlertCircle } from 'lucide-react';

interface Props {
  sections: UniqueSectionAnalysis;
  ruleLabel: string;
  color: 'blue' | 'green';
}

const UniqueSection: React.FC<Props> = ({ sections, ruleLabel, color }) => {
  const [showDetails, setShowDetails] = useState(false);

  const colorClasses = {
    blue: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-700',
      header: 'bg-blue-100',
      accent: 'border-blue-400'
    },
    green: {
      bg: 'bg-green-50',
      border: 'border-green-200', 
      text: 'text-green-700',
      header: 'bg-green-100',
      accent: 'border-green-400'
    }
  };

  const classes = colorClasses[color];

  return (
    <div className={`${classes.bg} ${classes.border} border rounded-lg p-4`}>
      <div className="flex items-center justify-between mb-3">
        <h4 className={`font-medium ${classes.text} flex items-center`}>
          <AlertCircle className="h-4 w-4 mr-2" />
          Unique to {ruleLabel} ({sections.sections.length} sections)
        </h4>
        {sections.sections.length > 0 && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className={`text-xs ${classes.text} hover:underline flex items-center`}
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
            {showDetails ? (
              <ChevronUp className="h-3 w-3 ml-1" />
            ) : (
              <ChevronDown className="h-3 w-3 ml-1" />
            )}
          </button>
        )}
      </div>

      {/* Analysis */}
      <div className="mb-4">
        <div 
          className={`${classes.header} p-3 rounded text-sm text-gray-700`}
          dangerouslySetInnerHTML={{ 
            __html: sections.analysis
              .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
              .replace(/\*(.*?)\*/g, '<em>$1</em>')
              .replace(/### (.*?)(\n|$)/g, '<h4 class="font-semibold mt-3 mb-2">$1</h4>')
              .replace(/\n\n/g, '</p><p class="mb-2">')
              .replace(/^(.+)$/gm, '<p class="mb-2">$1</p>')
          }}
        />
      </div>

      {/* Section Details */}
      {showDetails && sections.sections.length > 0 && (
        <div className="space-y-3">
          <h5 className={`text-sm font-medium ${classes.text} flex items-center`}>
            <FileText className="h-3 w-3 mr-1" />
            Section Details
          </h5>
          {sections.sections.map((section, index) => (
            <div 
              key={index} 
              className={`bg-white p-3 rounded border-l-4 ${classes.accent}`}
            >
              <div className="flex items-center justify-between mb-2">
                <h6 className="font-medium text-gray-800 text-sm">
                  {section.section_name}
                </h6>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {section.chunk_count} chunks
                </span>
              </div>
              <p className="text-xs text-gray-600 leading-relaxed">
                {section.summary}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UniqueSection;
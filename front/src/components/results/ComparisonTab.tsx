import React, { useState } from 'react';
import { useStore } from '../../store/store';
import { RefreshCw, AlertTriangle, CheckCircle, MinusCircle } from 'lucide-react';

// Sample comparison data
const sampleComparison = {
  title: 'FDA Guidance 2025 vs EMA Guidelines v3.2',
  sections: [
    {
      title: 'Safety Monitoring (§3)',
      changes: [
        {
          type: 'added',
          content: 'Daily assessment of serious adverse events required (FDA §3.2.1)',
          oldContent: 'Weekly assessment of serious adverse events (EMA §3.1.4)'
        },
        {
          type: 'modified',
          content: 'Centralized electronic monitoring system mandatory (FDA §3.2.3)',
          oldContent: 'Electronic or paper-based monitoring allowed (EMA §3.2.1)'
        },
        {
          type: 'unchanged',
          content: 'Safety committee review process (§3.5)'
        }
      ]
    },
    {
      title: 'Reporting Requirements (§4)',
      changes: [
        {
          type: 'added',
          content: '48-hour reporting window for critical incidents (FDA §4.3.2)',
          oldContent: '72-hour reporting window (EMA §4.2.1)'
        },
        {
          type: 'removed',
          content: 'Quarterly aggregate reports no longer required (EMA §4.5.3)'
        }
      ]
    }
  ]
};

const ComparisonTab: React.FC = () => {
  const { files, selectedFiles, setProcessing, setProcessingProgress } = useStore();
  const [comparison, setComparison] = useState<typeof sampleComparison | null>(null);
  const [expandedSections, setExpandedSections] = useState<string[]>([]);
  const [comparisonAspect, setComparisonAspect] = useState('safety');
  
  const selectedFileNames = selectedFiles
    .map(id => files.find(file => file.id === id)?.name || '')
    .filter(Boolean);
  
  const toggleSection = (sectionTitle: string) => {
    if (expandedSections.includes(sectionTitle)) {
      setExpandedSections(expandedSections.filter(title => title !== sectionTitle));
    } else {
      setExpandedSections([...expandedSections, sectionTitle]);
    }
  };
  
  const handleGenerateComparison = () => {
    // Simulate processing
    setProcessing(true);
    let progress = 0;
    
    const interval = setInterval(() => {
      progress += 5;
      setProcessingProgress(progress);
      
      if (progress >= 100) {
        clearInterval(interval);
        setProcessing(false);
        setProcessingProgress(0);
        setComparison(sampleComparison);
        setExpandedSections([sampleComparison.sections[0].title]); // Expand first section by default
      }
    }, 300);
  };
  
  const renderChangeIcon = (type: string) => {
    switch (type) {
      case 'added':
        return <CheckCircle className="h-4 w-4 text-success-500 flex-shrink-0 mt-0.5" />;
      case 'removed':
        return <MinusCircle className="h-4 w-4 text-error-500 flex-shrink-0 mt-0.5" />;
      case 'modified':
        return <AlertTriangle className="h-4 w-4 text-warning-500 flex-shrink-0 mt-0.5" />;
      default:
        return <div className="h-4 w-4 border border-neutral-300 rounded-full flex-shrink-0 mt-0.5" />;
    }
  };

  return (
    <div className="p-4 h-full flex flex-col">
      {comparison ? (
        <>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-neutral-800">{comparison.title}</h2>
            <button 
              className="p-1.5 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
              title="Regenerate comparison"
              onClick={handleGenerateComparison}
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
          
          <div className="space-y-4">
            {comparison.sections.map((section) => (
              <div 
                key={section.title} 
                className="border border-neutral-200 rounded-md overflow-hidden"
              >
                <div 
                  className="flex items-center justify-between p-3 bg-neutral-50 cursor-pointer"
                  onClick={() => toggleSection(section.title)}
                >
                  <h3 className="font-medium text-neutral-800">{section.title}</h3>
                  <svg 
                    className={`h-5 w-5 text-neutral-500 transition-transform ${
                      expandedSections.includes(section.title) ? 'transform rotate-180' : ''
                    }`} 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
                
                {expandedSections.includes(section.title) && (
                  <div className="p-3 bg-white">
                    <ul className="space-y-3">
                      {section.changes.map((change, idx) => (
                        <li key={idx} className="flex">
                          {renderChangeIcon(change.type)}
                          <div className="ml-2">
                            <p className={`text-sm ${
                              change.type === 'added' 
                                ? 'text-success-700' 
                                : change.type === 'removed' 
                                  ? 'text-error-700' 
                                  : change.type === 'modified' 
                                    ? 'text-warning-700' 
                                    : 'text-neutral-800'
                            }`}>
                              {change.content}
                            </p>
                            {change.oldContent && (
                              <p className="text-xs text-neutral-500 mt-1 line-through">
                                {change.oldContent}
                              </p>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center h-full text-center p-6">
          <div className="bg-primary-50 p-4 rounded-full mb-4">
            <DiffIcon className="h-8 w-8 text-primary-700" />
          </div>
          <h3 className="text-lg font-medium text-neutral-800 mb-2">Compare Documents</h3>
          <p className="text-neutral-500 mb-6">
            {selectedFiles.length < 2 
              ? 'Select at least two XML documents to compare.' 
              : `Compare ${selectedFileNames.join(' and ')} to see what's changed.`}
          </p>
          
          {selectedFiles.length >= 2 && (
            <>
              <div className="w-full max-w-md mb-4">
                <label htmlFor="comparison-aspect" className="block text-sm font-medium text-neutral-700 mb-1 text-left">
                  What aspect would you like to compare?
                </label>
                <select
                  id="comparison-aspect"
                  className="w-full p-2 border border-neutral-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  value={comparisonAspect}
                  onChange={(e) => setComparisonAspect(e.target.value)}
                >
                  <option value="safety">Safety Requirements</option>
                  <option value="monitoring">Monitoring Protocols</option>
                  <option value="reporting">Reporting Timelines</option>
                  <option value="all">All Changes</option>
                </select>
              </div>
              
              <button 
                className="px-4 py-2 bg-primary-700 hover:bg-primary-800 text-white rounded-md transition-colors flex items-center"
                onClick={handleGenerateComparison}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Generate Comparison
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
};

// Importing icon to use in component
import { DiffIcon } from 'lucide-react';

export default ComparisonTab;
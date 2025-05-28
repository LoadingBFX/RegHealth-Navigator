import React, { useState } from 'react';
import { useStore } from '../../store/store';
import { RefreshCw, Download, Copy, ExternalLink } from 'lucide-react';

const SummaryTab: React.FC = () => {
  const { summary, setSummary, setProcessing, setProcessingProgress } = useStore();
  const [expandedSections, setExpandedSections] = useState<string[]>([]);
  
  const toggleSection = (sectionId: string) => {
    if (expandedSections.includes(sectionId)) {
      setExpandedSections(expandedSections.filter(id => id !== sectionId));
    } else {
      setExpandedSections([...expandedSections, sectionId]);
    }
  };
  
  const handleGenerateSummary = () => {
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
      }
    }, 300);
  };
  
  const handleCopySummary = () => {
    if (!summary) return;
    
    let textToCopy = `# ${summary.title}\n\n`;
    
    summary.sections.forEach(section => {
      textToCopy += `## ${section.title}\n`;
      section.bullets.forEach(bullet => {
        textToCopy += `- ${bullet.content} ${bullet.citation}\n`;
      });
      textToCopy += '\n';
    });
    
    navigator.clipboard.writeText(textToCopy);
    // Would show toast notification in real implementation
  };

  return (
    <div className="p-4">
      {summary ? (
        <>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-neutral-800">{summary.title}</h2>
            <div className="flex space-x-1">
              <button 
                className="p-1.5 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
                title="Copy summary"
                onClick={handleCopySummary}
              >
                <Copy className="h-4 w-4" />
              </button>
              <button 
                className="p-1.5 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
                title="Download as markdown"
              >
                <Download className="h-4 w-4" />
              </button>
              <button 
                className="p-1.5 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
                title="Regenerate summary"
                onClick={handleGenerateSummary}
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
          </div>
          
          <div className="space-y-4">
            {summary.sections.map((section) => (
              <div 
                key={section.id} 
                className="border border-neutral-200 rounded-md overflow-hidden"
              >
                <div 
                  className="flex items-center justify-between p-3 bg-neutral-50 cursor-pointer"
                  onClick={() => toggleSection(section.id)}
                >
                  <h3 className="font-medium text-neutral-800">{section.title}</h3>
                  <svg 
                    className={`h-5 w-5 text-neutral-500 transition-transform ${
                      expandedSections.includes(section.id) ? 'transform rotate-180' : ''
                    }`} 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
                
                {expandedSections.includes(section.id) && (
                  <div className="p-3 bg-white">
                    <ul className="space-y-2">
                      {section.bullets.map((bullet) => (
                        <li key={bullet.id} className="flex items-start">
                          <span className="text-neutral-400 mr-2">•</span>
                          <span className="text-neutral-800">{bullet.content}</span>
                          <button 
                            className="ml-1 inline-flex items-center text-primary-600 text-sm hover:underline"
                            title="View source"
                          >
                            {bullet.citation}
                          </button>
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
            <ListChecks className="h-8 w-8 text-primary-700" />
          </div>
          <h3 className="text-lg font-medium text-neutral-800 mb-2">Generate a Summary</h3>
          <p className="text-neutral-500 mb-6">
            Create a concise summary of the selected XML documents with citations to the source material.
          </p>
          <button 
            className="px-4 py-2 bg-primary-700 hover:bg-primary-800 text-white rounded-md transition-colors flex items-center"
            onClick={handleGenerateSummary}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Generate Summary
          </button>
        </div>
      )}
    </div>
  );
};

// Importing icon to use in component
import { ListChecks } from 'lucide-react';

export default SummaryTab;
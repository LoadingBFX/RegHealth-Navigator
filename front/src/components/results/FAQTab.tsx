import React, { useState } from 'react';
import { useStore } from '../../store/store';
import { RefreshCw, Download, Copy, ExternalLink } from 'lucide-react';

const FAQTab: React.FC = () => {
  const { faq, setFAQ, setProcessing, setProcessingProgress } = useStore();
  const [expandedSections, setExpandedSections] = useState<string[]>([]);
  
  const toggleSection = (sectionId: string) => {
    if (expandedSections.includes(sectionId)) {
      setExpandedSections(expandedSections.filter(id => id !== sectionId));
    } else {
      setExpandedSections([...expandedSections, sectionId]);
    }
  };
  
  const handleGenerateFAQ = () => {
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
  
  const handleCopyFAQ = () => {
    if (!faq) return;
    
    let textToCopy = `# ${faq.title}\n\n`;
    
    faq.sections.forEach(section => {
      textToCopy += `## ${section.title}\n`;
      section.questions.forEach(qa => {
        textToCopy += `Q: ${qa.question}\n`;
        textToCopy += `A: ${qa.answer} ${qa.citation}\n\n`;
      });
      textToCopy += '\n';
    });
    
    navigator.clipboard.writeText(textToCopy);
    // Would show toast notification in real implementation
  };

  return (
    <div className="p-4">
      {faq ? (
        <>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-neutral-800">{faq.title}</h2>
            <div className="flex space-x-1">
              <button 
                className="p-1.5 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
                title="Copy FAQ"
                onClick={handleCopyFAQ}
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
                title="Regenerate FAQ"
                onClick={handleGenerateFAQ}
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
          </div>
          
          <div className="space-y-4">
            {faq.sections.map((section) => (
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
                    <div className="space-y-4">
                      {section.questions.map((qa, idx) => (
                        <div key={idx} className="space-y-2">
                          <p className="text-sm font-medium text-neutral-800">
                            Q: {qa.question}
                          </p>
                          <div className="flex items-start">
                            <span className="text-neutral-400 mr-2">A:</span>
                            <p className="text-sm text-neutral-700">{qa.answer}</p>
                            <button 
                              className="ml-1 inline-flex items-center text-primary-600 text-sm hover:underline"
                              title="View source"
                            >
                              {qa.citation}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
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
          <h3 className="text-lg font-medium text-neutral-800 mb-2">Generate FAQ</h3>
          <p className="text-neutral-500 mb-6">
            Create a list of frequently asked questions with answers based on the selected XML documents.
          </p>
          <button 
            className="px-4 py-2 bg-primary-700 hover:bg-primary-800 text-white rounded-md transition-colors flex items-center"
            onClick={handleGenerateFAQ}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Generate FAQ
          </button>
        </div>
      )}
    </div>
  );
};

// Importing icon to use in component
import { ListChecks } from 'lucide-react';

export default FAQTab;
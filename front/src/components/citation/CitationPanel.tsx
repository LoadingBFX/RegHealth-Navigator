import React, { useState } from 'react';
import { useStore } from '../../store/store';
import { X, ExternalLink, Maximize2 } from 'lucide-react';

const CitationPanel: React.FC = () => {
  const { citations, activeCitation, setActiveCitation } = useStore();
  const [showFullContent, setShowFullContent] = useState(false);
  
  const citation = activeCitation ? citations[activeCitation] : null;
  
  if (!citation) {
    return (
      <div className="w-80 bg-white border-l border-neutral-200 flex items-center justify-center">
        <div className="text-center p-6">
          <div className="bg-neutral-100 p-4 rounded-full mb-4 w-16 h-16 flex items-center justify-center mx-auto">
            <ExternalLink className="h-8 w-8 text-neutral-400" />
          </div>
          <h3 className="text-lg font-medium text-neutral-800 mb-2">No Citation Selected</h3>
          <p className="text-neutral-500 text-sm">
            Click on any citation link to view the source content here.
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <>
      <div className="w-80 bg-white border-l border-neutral-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-neutral-200 flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-medium text-neutral-800 truncate">{citation.id}</h3>
            <p className="text-sm text-neutral-500 truncate">{citation.documentName}</p>
          </div>
          <button
            onClick={() => setActiveCitation(null)}
            className="ml-2 p-1 text-neutral-400 hover:text-neutral-600 rounded"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 p-4 overflow-y-auto">
          <h4 className="font-medium text-neutral-800 mb-3">{citation.title}</h4>
          
          <div className="text-sm text-neutral-700 leading-relaxed">
            {citation.content}
            {citation.content !== citation.fullContent && (
              <>
                <span className="text-neutral-400">...</span>
                <button
                  onClick={() => setShowFullContent(true)}
                  className="ml-2 inline-flex items-center text-primary-600 hover:text-primary-700 text-sm"
                >
                  <Maximize2 className="h-3 w-3 mr-1" />
                  View Full
                </button>
              </>
            )}
          </div>
          
          <div className="mt-4 pt-4 border-t border-neutral-200">
            <div className="flex items-center text-xs text-neutral-500">
              <ExternalLink className="h-3 w-3 mr-1" />
              <span>Source: {citation.documentName}</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Full Content Modal */}
      {showFullContent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
            {/* Modal Header */}
            <div className="p-6 border-b border-neutral-200 flex items-center justify-between">
              <div>
                <h3 className="text-xl font-semibold text-neutral-800">{citation.id} - {citation.title}</h3>
                <p className="text-sm text-neutral-500 mt-1">{citation.documentName}</p>
              </div>
              <button
                onClick={() => setShowFullContent(false)}
                className="p-2 text-neutral-400 hover:text-neutral-600 rounded-full hover:bg-neutral-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            {/* Modal Content */}
            <div className="flex-1 p-6 overflow-y-auto">
              <div className="prose prose-sm max-w-none">
                <p className="text-neutral-700 leading-relaxed whitespace-pre-wrap">
                  {citation.fullContent}
                </p>
              </div>
            </div>
            
            {/* Modal Footer */}
            <div className="p-6 border-t border-neutral-200 bg-neutral-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center text-sm text-neutral-500">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  <span>Source: {citation.documentName}</span>
                </div>
                <button
                  onClick={() => setShowFullContent(false)}
                  className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default CitationPanel;
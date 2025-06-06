import React from 'react';
import { useStore } from '../../store/store';
import { X, ExternalLink } from 'lucide-react';

const CitationModal: React.FC = () => {
  const { showCitationModal, setShowCitationModal, activeCitation } = useStore();
  
  if (!showCitationModal || !activeCitation) {
    return null;
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
        {/* Modal Header */}
        <div className="p-6 border-b border-neutral-200 flex items-center justify-between">
          <div>
            <h3 className="text-xl font-semibold text-neutral-800">{activeCitation.id} - {activeCitation.title}</h3>
            <p className="text-sm text-neutral-500 mt-1">{activeCitation.documentName}</p>
          </div>
          <button
            onClick={() => setShowCitationModal(false)}
            className="p-2 text-neutral-400 hover:text-neutral-600 rounded-full hover:bg-neutral-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        {/* Modal Content */}
        <div className="flex-1 p-6 overflow-y-auto">
          <div className="prose prose-sm max-w-none">
            <p className="text-neutral-700 leading-relaxed whitespace-pre-wrap">
              {activeCitation.fullContent}
            </p>
          </div>
        </div>
        
        {/* Modal Footer */}
        <div className="p-6 border-t border-neutral-200 bg-neutral-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center text-sm text-neutral-500">
              <ExternalLink className="h-4 w-4 mr-2" />
              <span>Source: {activeCitation.documentName}</span>
            </div>
            <button
              onClick={() => setShowCitationModal(false)}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CitationModal;
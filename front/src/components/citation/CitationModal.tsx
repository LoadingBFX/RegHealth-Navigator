<<<<<<< HEAD
import React from 'react';
import { useStore } from '../../store/store';
import { X, ExternalLink } from 'lucide-react';

const CitationModal: React.FC = () => {
  const { showCitationModal, setShowCitationModal, activeCitation } = useStore();
=======
import React, { useState, useEffect } from 'react';
import { useStore } from '../../store/store';
import { X, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react';
import config from '../../config';

const CitationModal: React.FC = () => {
  const { showCitationModal, setShowCitationModal, activeCitation, messages, setActiveCitation } = useStore();
  const [currentSourceIndex, setCurrentSourceIndex] = useState(0);
  const [availableSources, setAvailableSources] = useState<any[]>([]);
  const [federalRegisterInfo, setFederalRegisterInfo] = useState<any>(null);
  const [isLoadingFederalInfo, setIsLoadingFederalInfo] = useState(false);

  // Get all sources from the latest assistant message
  useEffect(() => {
    if (showCitationModal) {
      const lastAssistantMessage = [...messages].reverse().find(msg => msg.role === 'assistant');
      if (lastAssistantMessage && lastAssistantMessage.sources) {
        setAvailableSources(lastAssistantMessage.sources);
        // Find current source index
        const index = lastAssistantMessage.sources.findIndex(s => s.name === activeCitation.documentName);
        setCurrentSourceIndex(index >= 0 ? index : 0);
      }

      // Fetch Federal Register info when modal opens
      const docId = extractDocIdFromFilename(activeCitation.documentName);
      if (docId) {
        setIsLoadingFederalInfo(true);
        setFederalRegisterInfo(null);
        
        fetch(`${config.api.baseUrl}/api/federal-register/${docId}`)
          .then(response => response.json())
          .then(data => {
            if (!data.error) {
              setFederalRegisterInfo(data);
            }
          })
          .catch(error => {
            console.error('Error fetching Federal Register info:', error);
          })
          .finally(() => {
            setIsLoadingFederalInfo(false);
          });
      }
    }
  }, [showCitationModal, activeCitation, messages]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (!showCitationModal) return;
      
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        if (currentSourceIndex > 0 && availableSources.length > 0) {
          const prevSource = availableSources[currentSourceIndex - 1];
          const citationData = {
            id: prevSource.name,
            title: formatSourceName(prevSource.name),
            content: prevSource.chunks.map((chunk: any) => chunk.text).join('\n\n...\n\n'),
            fullContent: prevSource.chunks.map((chunk: any) => chunk.text).join('\n\n...\n\n'),
            documentId: prevSource.name,
            documentName: prevSource.name
          };
          setActiveCitation(citationData);
          setCurrentSourceIndex(currentSourceIndex - 1);
        }
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        if (currentSourceIndex < availableSources.length - 1 && availableSources.length > 0) {
          const nextSource = availableSources[currentSourceIndex + 1];
          const citationData = {
            id: nextSource.name,
            title: formatSourceName(nextSource.name),
            content: nextSource.chunks.map((chunk: any) => chunk.text).join('\n\n...\n\n'),
            fullContent: nextSource.chunks.map((chunk: any) => chunk.text).join('\n\n...\n\n'),
            documentId: nextSource.name,
            documentName: nextSource.name
          };
          setActiveCitation(citationData);
          setCurrentSourceIndex(currentSourceIndex + 1);
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        setShowCitationModal(false);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [showCitationModal, currentSourceIndex, availableSources, setActiveCitation, setShowCitationModal]);

  // Navigation functions
  const goToPrevious = () => {
    if (currentSourceIndex > 0 && availableSources.length > 0) {
      const prevSource = availableSources[currentSourceIndex - 1];
      const citationData = {
        id: prevSource.name,
        title: formatSourceName(prevSource.name),
        content: prevSource.chunks.map((chunk: any) => chunk.text).join('\n\n...\n\n'),
        fullContent: prevSource.chunks.map((chunk: any) => chunk.text).join('\n\n...\n\n'),
        documentId: prevSource.name,
        documentName: prevSource.name
      };
      setActiveCitation(citationData);
      setCurrentSourceIndex(currentSourceIndex - 1);
    }
  };

  const goToNext = () => {
    if (currentSourceIndex < availableSources.length - 1 && availableSources.length > 0) {
      const nextSource = availableSources[currentSourceIndex + 1];
      const citationData = {
        id: nextSource.name,
        title: formatSourceName(nextSource.name),
        content: nextSource.chunks.map((chunk: any) => chunk.text).join('\n\n...\n\n'),
        fullContent: nextSource.chunks.map((chunk: any) => chunk.text).join('\n\n...\n\n'),
        documentId: nextSource.name,
        documentName: nextSource.name
      };
      setActiveCitation(citationData);
      setCurrentSourceIndex(currentSourceIndex + 1);
    }
  };

  const formatSourceName = (filename: string): string => {
    if (!filename || !filename.endsWith('.xml')) {
      return filename;
    }
    
    const nameWithoutExt = filename.slice(0, -4);
    const parts = nameWithoutExt.split('_');
    
    if (parts.length >= 4) {
      const year = parts[0];
      const program = parts[1];
      const type = parts[2];
      const docId = parts[3];
      return `${year} ${program} ${type}, Doc id: ${docId}`;
    }
    return filename;
  };

  const extractDocIdFromFilename = (filename: string): string | null => {
    if (!filename || !filename.endsWith('.xml')) {
      return null;
    }
    
    const nameWithoutExt = filename.slice(0, -4);
    const parts = nameWithoutExt.split('_');
    
    if (parts.length >= 4) {
      return parts[3]; // This is the doc_number like "2024-06431"
    }
    return null;
  };

  const removeFileExtension = (filename: string): string => {
    return filename.endsWith('.xml') ? filename.slice(0, -4) : filename;
  };

  const getBestDocumentUrl = (): { url: string; text: string; } | null => {
    if (!federalRegisterInfo) return null;

    // Prefer HTML URL
    if (federalRegisterInfo.html_url) {
      return {
        url: federalRegisterInfo.html_url,
        text: "View on Federal Register"
      };
    }

    // Fallback to PDF URL
    if (federalRegisterInfo.pdf_url) {
      return {
        url: federalRegisterInfo.pdf_url,
        text: "View PDF on GovInfo"
      };
    }

    return null;
  };
>>>>>>> dev
  
  if (!showCitationModal || !activeCitation) {
    return null;
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
        {/* Modal Header */}
        <div className="p-6 border-b border-neutral-200 flex items-center justify-between">
<<<<<<< HEAD
          <div>
            <h3 className="text-xl font-semibold text-neutral-800">{activeCitation.id} - {activeCitation.title}</h3>
            <p className="text-sm text-neutral-500 mt-1">{activeCitation.documentName}</p>
          </div>
=======
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-neutral-800">{formatSourceName(activeCitation.documentName)}</h3>
            {availableSources.length > 1 && (
              <p className="text-sm text-neutral-500 mt-1">
                Source {currentSourceIndex + 1} of {availableSources.length}
              </p>
            )}
          </div>
          
          {/* Navigation Controls */}
          {availableSources.length > 1 && (
            <div className="flex items-center space-x-2 mr-4">
              <button
                onClick={goToPrevious}
                disabled={currentSourceIndex === 0}
                className="p-2 text-neutral-400 hover:text-neutral-600 rounded-full hover:bg-neutral-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <button
                onClick={goToNext}
                disabled={currentSourceIndex === availableSources.length - 1}
                className="p-2 text-neutral-400 hover:text-neutral-600 rounded-full hover:bg-neutral-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>
          )}
          
>>>>>>> dev
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
<<<<<<< HEAD
              <span>Source: {activeCitation.documentName}</span>
=======
              {isLoadingFederalInfo ? (
                <span className="text-neutral-400">Loading document info...</span>
              ) : getBestDocumentUrl() ? (
                <a 
                  href={getBestDocumentUrl()!.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:text-primary-700 hover:underline transition-colors"
                >
                  {getBestDocumentUrl()!.text}: {removeFileExtension(activeCitation.documentName)}
                </a>
              ) : extractDocIdFromFilename(activeCitation.documentName) ? (
                <a 
                  href={`https://www.federalregister.gov/documents/${extractDocIdFromFilename(activeCitation.documentName)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:text-primary-700 hover:underline transition-colors"
                >
                  View on Federal Register: {removeFileExtension(activeCitation.documentName)}
                </a>
              ) : (
                <span>Document: {activeCitation.documentName}</span>
              )}
>>>>>>> dev
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
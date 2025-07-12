import React, { useState, useEffect } from 'react';
import { useStore } from '../../store/store';
import { RefreshCw, Download, Copy, FileText, ChevronLeft, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import config from '../../config';

interface Document {
  id: string;
  name: string;
  program: string;
  year: string;
  type: string;
  size: string;
  date: string;
}

interface Summary {
  title: string;
  document_name: string;
  content: string;
  sections: Array<{
    title: string;
    content: string;
  }>;
}

const SummaryTab: React.FC = () => {
  const { 
    citations,
    setActiveCitation,
    setShowCitationModal,
    setProcessing, 
    setProcessingProgress
  } = useStore();
  
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [selectedSummary, setSelectedSummary] = useState<Summary | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const itemsPerPage = 10;
  
  // Pagination logic
  const totalPages = Math.ceil(documents.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentFiles = documents.slice(startIndex, endIndex);
  
  // Fetch documents from backend
  useEffect(() => {
    const fetchDocuments = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${config.api.baseUrl}${config.api.endpoints.availableSummaries}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setDocuments(data.summaries || []);
      } catch (err) {
        console.error('Error fetching documents:', err);
        setError('Failed to load documents. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, []);
  
  const selectedDocument = selectedDocumentId ? documents.find(f => f.id === selectedDocumentId) : null;
  
  const handleGenerateSummary = async () => {
    if (!selectedDocumentId) return;
    
    setProcessing(true);
    setProcessingProgress(0);
    
    try {
      const response = await fetch(`${config.api.baseUrl}${config.api.endpoints.getSummary}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          doc_name: selectedDocumentId
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setSelectedSummary(data.summary);
      
      // Simulate progress
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        setProcessingProgress(progress);
        
        if (progress >= 100) {
          clearInterval(interval);
          setProcessing(false);
          setProcessingProgress(0);
        }
      }, 100);
      
    } catch (err) {
      console.error('Error generating summary:', err);
      setProcessing(false);
      setProcessingProgress(0);
      setError('Failed to generate summary. Please try again.');
    }
  };
  
  const handleCopySummary = () => {
    if (selectedSummary?.content) {
      navigator.clipboard.writeText(selectedSummary.content);
    }
  };

  const handleCitationClick = (citationId: string) => {
    const citation = citations[citationId];
    if (citation) {
      setActiveCitation(citation);
      setShowCitationModal(true);
    }
  };

  const goToPage = (page: number) => {
    setCurrentPage(page);
  };

  const goToPrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const goToNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handleDocumentSelect = async (documentId: string) => {
    setSelectedDocumentId(documentId);
    setSelectedSummary(null); // Clear previous summary
    
    // Auto-generate summary when document is selected
    setProcessing(true);
    setProcessingProgress(0);
    
    try {
      const response = await fetch(`${config.api.baseUrl}${config.api.endpoints.getSummary}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          doc_name: documentId
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setSelectedSummary(data.summary);
      
      // Simulate progress
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        setProcessingProgress(progress);
        
        if (progress >= 100) {
          clearInterval(interval);
          setProcessing(false);
          setProcessingProgress(0);
        }
      }, 100);
      
    } catch (err) {
      console.error('Error generating summary:', err);
      setProcessing(false);
      setProcessingProgress(0);
      setError('Failed to generate summary. Please try again.');
    }
  };

  return (
    <div className="flex-1 flex h-full">
      {/* Left Sidebar - Document List (20%) */}
      <div className="w-1/5 bg-white border-r border-neutral-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-neutral-200">
          <h3 className="text-lg font-medium text-neutral-800 flex items-center">
            <FileText className="h-5 w-5 mr-2 text-primary-600" />
            Documents
          </h3>
          <p className="text-sm text-neutral-500 mt-1">
            {loading ? 'Loading...' : `${documents.length} documents available`}
          </p>
        </div>
        
        {/* Document List */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-2">
            {loading ? (
              <div className="p-4 text-center text-neutral-500">
                Loading documents...
              </div>
            ) : error ? (
              <div className="p-4 text-center text-red-500">
                {error}
              </div>
            ) : currentFiles.length === 0 ? (
              <div className="p-4 text-center text-neutral-500">
                No documents found
              </div>
            ) : (
              currentFiles.map((file) => (
                <div
                  key={file.id}
                  className={`p-3 mb-2 rounded-lg cursor-pointer transition-colors ${
                    selectedDocumentId === file.id
                      ? 'bg-primary-50 border border-primary-200'
                      : 'hover:bg-neutral-50 border border-transparent'
                  }`}
                  onClick={() => handleDocumentSelect(file.id)}
                >
                  <h4 className="text-sm font-medium text-neutral-800 mb-1 line-clamp-2">
                    {file.name}
                  </h4>
                  <div className="flex justify-between text-xs text-neutral-500">
                    <span>{file.size}</span>
                    <span>{file.year}</span>
                  </div>
                  <div className="text-xs text-neutral-400 mt-1">
                    {file.program} • {file.type}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-neutral-200">
            <div className="flex items-center justify-between">
              <button
                onClick={goToPrevPage}
                disabled={currentPage === 1}
                className="p-1 rounded hover:bg-neutral-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              
              <div className="flex space-x-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => goToPage(page)}
                    className={`px-2 py-1 text-xs rounded ${
                      currentPage === page
                        ? 'bg-primary-600 text-white'
                        : 'hover:bg-neutral-100'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>
              
              <button
                onClick={goToNextPage}
                disabled={currentPage === totalPages}
                className="p-1 rounded hover:bg-neutral-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
            
            <p className="text-xs text-neutral-500 text-center mt-2">
              Page {currentPage} of {totalPages}
            </p>
          </div>
        )}
      </div>
      
      {/* Right Content - Summary Display (80%) */}
      <div className="flex-1 flex flex-col">
        {selectedDocument ? (
          <>
            {/* Header */}
            <div className="p-6 border-b border-neutral-200 bg-white">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-semibold text-neutral-800">Document Summary</h2>
                  <p className="text-sm text-neutral-500 mt-1">
                    {selectedDocument.year} • {selectedDocument.program} • {selectedDocument.type}
                  </p>
                </div>
                {/* Removed Copy, Download, and Refresh buttons */}
              </div>
            </div>
            
            {/* Summary Content */}
            <div className="flex-1 overflow-y-auto p-6 bg-neutral-50">
              <div className="max-w-4xl mx-auto">
                {selectedSummary ? (
                  <div className="bg-white rounded-lg shadow-sm p-8">
                    <div className="prose prose-lg max-w-none">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        className="markdown-content"
                        components={{
                          // Custom styling for markdown elements
                          h1: ({node, ...props}) => <h1 className="text-3xl font-bold text-neutral-900 mb-4" {...props} />,
                          h2: ({node, ...props}) => <h2 className="text-2xl font-semibold text-neutral-800 mb-3 mt-6" {...props} />,
                          h3: ({node, ...props}) => <h3 className="text-xl font-medium text-neutral-700 mb-2 mt-4" {...props} />,
                          h4: ({node, ...props}) => <h4 className="text-lg font-medium text-neutral-700 mb-2 mt-3" {...props} />,
                          p: ({node, ...props}) => <p className="text-neutral-700 leading-relaxed mb-4" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc list-inside text-neutral-700 mb-4 space-y-1" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal list-inside text-neutral-700 mb-4 space-y-1" {...props} />,
                          li: ({node, ...props}) => <li className="text-neutral-700" {...props} />,
                          strong: ({node, ...props}) => <strong className="font-semibold text-neutral-800" {...props} />,
                          em: ({node, ...props}) => <em className="italic text-neutral-700" {...props} />,
                          code: ({node, inline, ...props}: any) => 
                            inline ? 
                              <code className="bg-neutral-100 px-1 py-0.5 rounded text-sm font-mono text-neutral-800" {...props} /> :
                              <code className="block bg-neutral-100 p-3 rounded text-sm font-mono text-neutral-800 overflow-x-auto" {...props} />,
                          pre: ({node, ...props}) => <pre className="bg-neutral-100 p-3 rounded text-sm font-mono text-neutral-800 overflow-x-auto mb-4" {...props} />,
                          blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-primary-500 pl-4 italic text-neutral-600 mb-4" {...props} />,
                          table: ({node, ...props}) => <table className="w-full border-collapse border border-neutral-300 mb-4" {...props} />,
                          th: ({node, ...props}) => <th className="border border-neutral-300 px-3 py-2 bg-neutral-50 font-semibold text-left" {...props} />,
                          td: ({node, ...props}) => <td className="border border-neutral-300 px-3 py-2" {...props} />,
                        }}
                      >
                        {selectedSummary.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white rounded-lg shadow-sm p-8">
                    <div className="text-center text-neutral-500">
                      {error ? (
                        <div className="text-red-500">{error}</div>
                      ) : (
                        <div>Generating summary...</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          /* No Document Selected */
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <div className="bg-primary-50 p-6 rounded-full mb-6">
              <FileText className="h-12 w-12 text-primary-700" />
            </div>
            <h3 className="text-2xl font-medium text-neutral-800 mb-4">Select a Document</h3>
            <p className="text-neutral-500 text-center max-w-md">
              Choose a document from the list on the left to view its summary. 
              The summary provides key insights and important information extracted from the document.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SummaryTab;
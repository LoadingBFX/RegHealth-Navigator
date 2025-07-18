import React, { useState, useEffect, useMemo } from 'react';
import { useStore } from '../../store/store';
import { RefreshCw, Download, Copy, FileText, ChevronLeft, ChevronRight, Search, Filter } from 'lucide-react';
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
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProgram, setSelectedProgram] = useState('all');
  const [selectedYear, setSelectedYear] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [showCopySuccess, setShowCopySuccess] = useState(false);
  const [isGridView, setIsGridView] = useState(true);
  const itemsPerPage = 10;
  
  // Filter and search logic
  const filteredDocuments = useMemo(() => {
    return documents.filter(doc => {
      const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesProgram = selectedProgram === 'all' || doc.program === selectedProgram;
      const matchesYear = selectedYear === 'all' || doc.year === selectedYear;
      const matchesType = selectedType === 'all' || doc.type === selectedType;
      
      return matchesSearch && matchesProgram && matchesYear && matchesType;
    });
  }, [documents, searchTerm, selectedProgram, selectedYear, selectedType]);
  
  // Get unique values for filters
  const uniquePrograms = useMemo(() => [...new Set(documents.map(doc => doc.program))], [documents]);
  const uniqueYears = useMemo(() => [...new Set(documents.map(doc => doc.year))].sort().reverse(), [documents]);
  const uniqueTypes = useMemo(() => [...new Set(documents.map(doc => doc.type))], [documents]);
  
  // Pagination logic for grid view
  const itemsPerPageGrid = 12; // More items per page for grid
  const totalPages = Math.ceil(filteredDocuments.length / itemsPerPageGrid);
  const startIndex = (currentPage - 1) * itemsPerPageGrid;
  const endIndex = startIndex + itemsPerPageGrid;
  const currentFiles = filteredDocuments.slice(startIndex, endIndex);
  
  // Pagination for split view sidebar
  const currentFilesSidebar = filteredDocuments.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);
  
  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedProgram, selectedYear, selectedType]);
  
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
  
  const handleDownloadSummary = () => {
    if (!selectedSummary) return;
    
    const blob = new Blob([selectedSummary.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedSummary.title || 'summary'}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  const handleCopySummary = async () => {
    if (!selectedSummary?.content) return;
    
    try {
      await navigator.clipboard.writeText(selectedSummary.content);
      setShowCopySuccess(true);
      setTimeout(() => setShowCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy summary:', err);
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
    setSelectedSummary(null);
    setError(null);
    setLoading(true);
    setIsGridView(false); // Switch to split view
    
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
      
    } catch (err) {
      console.error('Error loading summary:', err);
      setError('Failed to load summary. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Grid view for all documents
  const renderGridView = () => (
    <div className="flex-1 p-6 bg-gray-50 overflow-y-auto h-full">
      {/* Header */}
      <div className="max-w-3xl mx-auto w-full px-4">
        <div className="mb-6 bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="bg-pink-100 p-2 rounded-lg mr-3">
                <FileText className="h-5 w-5 text-pink-600" />
              </div>
              <h2 className="text-lg font-medium text-neutral-800">Document Summaries</h2>
            </div>
            <div className="bg-teal-50 px-3 py-1 rounded-full border border-teal-200">
              <p className="text-sm text-teal-700 font-medium">
                {loading ? 'Loading...' : `${filteredDocuments.length} of ${documents.length} documents available`}
              </p>
            </div>
          </div>
          <p className="text-sm text-neutral-500 mt-3 ml-12">
            Browse and review summaries of regulatory documents. Select a document for detailed analysis.
          </p>
        </div>
      </div>
      
      {/* Document Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-6">
        {loading ? (
          [...Array(8)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6 animate-pulse">
              <div className="flex items-start justify-between mb-4">
                <div className="h-5 bg-neutral-200 rounded w-3/4"></div>
                <div className="flex space-x-2">
                  <div className="w-3 h-3 bg-neutral-200 rounded-full"></div>
                  <div className="w-3 h-3 bg-neutral-200 rounded-full"></div>
                </div>
              </div>
              <div className="space-y-2 mb-4">
                <div className="h-3 bg-neutral-200 rounded w-full"></div>
                <div className="h-3 bg-neutral-200 rounded w-2/3"></div>
              </div>
              <div className="flex justify-between items-center">
                <div className="h-4 bg-neutral-200 rounded w-16"></div>
                <div className="h-4 bg-neutral-200 rounded w-12"></div>
              </div>
            </div>
          ))
        ) : error ? (
          <div className="col-span-full text-center py-12">
            <div className="text-red-500 text-lg">{error}</div>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <div className="text-neutral-500 text-lg">No documents found</div>
          </div>
        ) : (
          currentFiles.map((file) => (
            <div
              key={file.id}
              className="bg-white rounded-2xl border-2 transition-all duration-300 cursor-pointer group overflow-hidden relative hover:shadow-lg"
              style={{
                borderColor: file.type.toLowerCase().includes('final') ? '#FFB6C1' : // 马卡龙粉
                            file.type.toLowerCase().includes('proposed') ? '#FFE4B5' : // 马卡龙黄
                            file.type.toLowerCase().includes('notice') ? '#E6E6FA' : // 马卡龙紫
                            '#D3D3D3'
              }}
              onClick={() => handleDocumentSelect(file.id)}
            >
              <div className="p-4">
                {/* 文件名 */}
                <div className="text-center">
                  <h3 className="text-sm font-medium text-gray-800 leading-tight flex items-center justify-center">
                    <span>{file.year}</span>
                    <span className="mx-1.5 text-gray-400">•</span>
                    <span>{file.program}</span>
                    <span className="mx-1.5 text-gray-400">•</span>
                    <span>{file.type.toLowerCase().includes('final') ? 'Final' : file.type.toLowerCase().includes('proposed') ? 'Proposed' : 'Notice'}</span>
                  </h3>
                </div>
              </div>
              
              {/* 右下角类型指示条 */}
              <div 
                className="absolute bottom-0 right-0 w-8 h-1.5 rounded-tl-lg"
                style={{
                  backgroundColor: 
                    file.type.toLowerCase().includes('final') ? '#FFB6C1' : // 马卡龙粉
                    file.type.toLowerCase().includes('proposed') ? '#FFE4B5' : // 马卡龙黄
                    file.type.toLowerCase().includes('notice') ? '#E6E6FA' : // 马卡龙紫
                    '#D3D3D3'
                }}
              ></div>
            </div>
          ))
        )}
      </div>
      
      {/* Pagination for Grid View - Only show if more than one page */}
      {filteredDocuments.length > itemsPerPageGrid && (
        <div className="flex justify-center mt-6">
          <div className="flex items-center space-x-2">
            <button
              onClick={goToPrevPage}
              disabled={currentPage === 1}
              className="px-3 py-2 text-sm bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </button>
            
            <div className="flex space-x-1">
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                let page;
                if (totalPages <= 5) {
                  page = i + 1;
                } else if (currentPage <= 3) {
                  page = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  page = totalPages - 4 + i;
                } else {
                  page = currentPage - 2 + i;
                }
                
                return (
                  <button
                    key={page}
                    onClick={() => goToPage(page)}
                    className={`px-3 py-2 text-sm rounded-lg ${
                      currentPage === page
                        ? 'bg-primary-600 text-white'
                        : 'bg-white border border-neutral-300 hover:bg-neutral-50'
                    }`}
                  >
                    {page}
                  </button>
                );
              })}
            </div>
            
            <button
              onClick={goToNextPage}
              disabled={currentPage === totalPages}
              className="px-3 py-2 text-sm bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
  
  // Split view for selected document
  const renderSplitView = () => (
    <div className="flex-1 flex h-full">
      {/* Left Sidebar - Document List (20%) */}
      <div className="w-1/5 bg-white border-r border-neutral-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-neutral-200">
          <button
            onClick={() => {
              setIsGridView(true);
              setSelectedDocumentId(null);
              setSelectedSummary(null);
            }}
            className="w-full bg-neutral-100 hover:bg-neutral-200 text-neutral-700 px-3 py-2 rounded-lg transition-colors mb-3 text-sm"
          >
            ← Back to Grid
          </button>
          <h3 className="text-lg font-medium text-neutral-800 flex items-center">
            <FileText className="h-5 w-5 mr-2 text-primary-600" />
            Documents
          </h3>
          <p className="text-sm text-neutral-500 mt-1">
            {loading ? 'Loading...' : `${filteredDocuments.length} of ${documents.length} documents`}
          </p>
          
          {/* Search */}
          <div className="mt-3 relative">
            <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          
          {/* Filters */}
          <div className="mt-3 space-y-2">
            <select
              value={selectedProgram}
              onChange={(e) => setSelectedProgram(e.target.value)}
              className="w-full p-2 border border-neutral-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Programs</option>
              {uniquePrograms.map(program => (
                <option key={program} value={program}>{program}</option>
              ))}
            </select>
            
            <div className="flex space-x-2">
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(e.target.value)}
                className="flex-1 p-2 border border-neutral-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">All Years</option>
                {uniqueYears.map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
              
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="flex-1 p-2 border border-neutral-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">All Types</option>
                {uniqueTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
        
        {/* Document List */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-3">
            {loading ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="bg-white rounded-lg border border-neutral-200 p-4 animate-pulse">
                    <div className="flex items-start justify-between mb-2">
                      <div className="h-4 bg-neutral-200 rounded w-3/4"></div>
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-neutral-200 rounded-full"></div>
                        <div className="w-2 h-2 bg-neutral-200 rounded-full"></div>
                      </div>
                    </div>
                    <div className="flex justify-between mb-2">
                      <div className="h-3 bg-neutral-200 rounded w-16"></div>
                      <div className="h-3 bg-neutral-200 rounded w-12"></div>
                    </div>
                    <div className="h-3 bg-neutral-200 rounded w-24"></div>
                  </div>
                ))}
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
              <div className="space-y-3">
                {currentFilesSidebar.map((file) => (
                  <div
                    key={file.id}
                    className={`bg-white rounded-xl border-2 transition-all duration-200 cursor-pointer relative overflow-hidden ${
                      selectedDocumentId === file.id
                        ? 'ring-2 ring-blue-200 shadow-md'
                        : 'hover:shadow-sm'
                    }`}
                    style={{
                      borderColor: file.type.toLowerCase().includes('final') ? '#FFB6C1' : // 马卡龙粉
                                  file.type.toLowerCase().includes('proposed') ? '#FFE4B5' : // 马卡龙黄
                                  file.type.toLowerCase().includes('notice') ? '#E6E6FA' : // 马卡龙紫
                                  '#D3D3D3'
                    }}
                    onClick={() => handleDocumentSelect(file.id)}
                  >
                    <div className="p-3">
                      {/* 文件名 */}
                      <div className="text-center">
                        <h4 className="text-xs font-medium text-gray-800 leading-tight flex items-center justify-center">
                          <span>{file.year}</span>
                          <span className="mx-1 text-gray-400">•</span>
                          <span>{file.program}</span>
                          <span className="mx-1 text-gray-400">•</span>
                          <span>{file.type.toLowerCase().includes('final') ? 'Final' : file.type.toLowerCase().includes('proposed') ? 'Proposed' : 'Notice'}</span>
                        </h4>
                      </div>
                    </div>
                    
                    {/* 右下角类型指示条 */}
                    <div 
                      className="absolute bottom-0 right-0 w-6 h-1.5 rounded-tl"
                      style={{
                        backgroundColor: 
                          file.type.toLowerCase().includes('final') ? '#FFB6C1' : // 马卡龙粉
                          file.type.toLowerCase().includes('proposed') ? '#FFE4B5' : // 马卡龙黄
                          file.type.toLowerCase().includes('notice') ? '#E6E6FA' : // 马卡龙紫
                          '#D3D3D3'
                      }}
                    ></div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* Sidebar Pagination */}
        {Math.ceil(filteredDocuments.length / itemsPerPage) > 1 && (
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
                {Array.from({ length: Math.ceil(filteredDocuments.length / itemsPerPage) }, (_, i) => i + 1).map((page) => (
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
                disabled={currentPage === Math.ceil(filteredDocuments.length / itemsPerPage)}
                className="p-1 rounded hover:bg-neutral-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
            
            <p className="text-xs text-neutral-500 text-center mt-2">
              Page {currentPage} of {Math.ceil(filteredDocuments.length / itemsPerPage)}
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
                  <div className="flex items-center space-x-3">
                    <h2 className="text-2xl font-semibold text-gray-800">Document Summary</h2>
                    <div 
                      className="w-4 h-4 rounded-full"
                      style={{
                        backgroundColor: 
                          selectedDocument.type.toLowerCase().includes('final') ? '#FFB6C1' : // 马卡龙粉
                          selectedDocument.type.toLowerCase().includes('proposed') ? '#FFE4B5' : // 马卡龙黄
                          selectedDocument.type.toLowerCase().includes('notice') ? '#E6E6FA' : // 马卡龙紫
                          '#D3D3D3'
                      }}
                      title={selectedDocument.type}
                    ></div>
                  </div>
                  <div className="mt-2">
                    <span className="text-sm font-medium text-gray-700 flex items-center">
                      <span>{selectedDocument.year}</span>
                      <span className="mx-2 text-gray-400">•</span>
                      <span>{selectedDocument.program}</span>
                      <span className="mx-2 text-gray-400">•</span>
                      <span>{selectedDocument.type.toLowerCase().includes('final') ? 'Final' : selectedDocument.type.toLowerCase().includes('proposed') ? 'Proposed' : 'Notice'}</span>
                    </span>
                  </div>
                </div>
                {selectedSummary && (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleCopySummary}
                      className={`flex items-center px-3 py-2 text-sm rounded-lg transition-all duration-200 ${
                        showCopySuccess 
                          ? 'bg-green-100 text-green-700 border border-green-300' 
                          : 'bg-neutral-100 hover:bg-neutral-200 text-neutral-700'
                      }`}
                    >
                      <Copy className="h-4 w-4 mr-1" />
                      {showCopySuccess ? 'Copied!' : 'Copy'}
                    </button>
                    <button
                      onClick={handleDownloadSummary}
                      className="flex items-center px-3 py-2 text-sm bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </button>
                  </div>
                )}
              </div>
            </div>
            
            {/* Summary Content */}
            <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
              <div className="max-w-4xl mx-auto">
                {selectedSummary ? (
                  <div className="bg-white rounded-lg shadow-sm p-8 border-2" style={{
                    borderColor: selectedDocument.type.toLowerCase().includes('final') ? '#FFB6C1' : 
                                selectedDocument.type.toLowerCase().includes('proposed') ? '#FFE4B5' : 
                                selectedDocument.type.toLowerCase().includes('notice') ? '#E6E6FA' : 
                                '#D3D3D3'
                  }}>
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
                      ) : loading ? (
                        <div>Loading summary...</div>
                      ) : (
                        <div>No summary available</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          /* Back to Grid Button */
          <div className="flex-1 flex flex-col items-center justify-center min-h-[400px] text-center px-4">
            <button
              onClick={() => {
                setIsGridView(true);
                setSelectedDocumentId(null);
                setSelectedSummary(null);
              }}
              className="bg-primary-600 hover:bg-primary-700 text-white px-4 sm:px-6 py-2 sm:py-3 rounded-lg transition-colors mb-4 text-sm sm:text-base"
            >
              ← Back to All Documents
            </button>
            <div className="bg-primary-50 p-4 sm:p-6 rounded-full mb-4 sm:mb-6">
              <FileText className="h-8 w-8 sm:h-12 sm:w-12 text-primary-700" />
            </div>
            <h3 className="text-lg sm:text-2xl font-medium text-neutral-800 mb-2 sm:mb-4">Select a Document</h3>
            <p className="text-neutral-500 text-center text-sm sm:text-base max-w-sm sm:max-w-md lg:max-w-lg">
              Choose a document from the list on the left to view its summary.
            </p>
          </div>
        )}
      </div>
    </div>
  );
  
  return isGridView ? renderGridView() : renderSplitView();
};

export default SummaryTab;
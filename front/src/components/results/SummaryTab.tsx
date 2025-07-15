<<<<<<< HEAD
import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/store';
import { RefreshCw, Download, Copy, FileText, Search, Filter, X } from 'lucide-react';

const SummaryTab: React.FC = () => {
  const { 
    summary, 
    setSummary, 
    setProcessing, 
    setProcessingProgress, 
    citations,
    setActiveCitation,
    setShowCitationModal,
    selectedFiles,
    setSelectedFiles,
    files,
    searchTerm,
    setSearchTerm,
    yearFilter,
    setYearFilter,
    programFilter,
    setProgramFilter,
    typeFilter,
    setTypeFilter,
    showFilters,
    setShowFilters
  } = useStore();
  
  const [expandedSections, setExpandedSections] = useState<string[]>(['1']);
  const [showDocumentSelector, setShowDocumentSelector] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  
  const programs = ['MPFS', 'HOSPICE', 'SNF', 'QPP'];
  const types = ['final', 'proposed'];
  const years = ['2024', '2023', '2022', '2021'];
  
  const selectedFileNames = selectedFiles
    .map(id => files.find(file => file.id === id)?.name || '')
    .filter(Boolean);
  
  // Filter files based on search and filters
  const filteredFiles = files.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesYear = yearFilter === 'all' || file.name.includes(yearFilter);
    const matchesProgram = programFilter === 'all' || file.name.includes(programFilter);
    const matchesType = typeFilter === 'all' || file.name.includes(typeFilter);
    return matchesSearch && matchesYear && matchesProgram && matchesType;
  });
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowDocumentSelector(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  const toggleSection = (sectionId: string) => {
    if (expandedSections.includes(sectionId)) {
      setExpandedSections(expandedSections.filter(id => id !== sectionId));
    } else {
      setExpandedSections([...expandedSections, sectionId]);
    }
  };
  
  const handleGenerateSummary = () => {
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
=======
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
>>>>>>> dev
  };

  const handleCitationClick = (citationId: string) => {
    const citation = citations[citationId];
    if (citation) {
      setActiveCitation(citation);
      setShowCitationModal(true);
    }
  };

<<<<<<< HEAD
  const handleFileSelect = (fileId: string) => {
    if (selectedFiles.includes(fileId)) {
      setSelectedFiles(selectedFiles.filter(id => id !== fileId));
    } else {
      setSelectedFiles([...selectedFiles, fileId]);
    }
  };
  
  const removeSelectedFile = (fileId: string) => {
    setSelectedFiles(selectedFiles.filter(id => id !== fileId));
  };
  
  const clearAllFilters = () => {
    setSearchTerm('');
    setYearFilter('all');
    setProgramFilter('all');
    setTypeFilter('all');
  };
  
  const hasActiveFilters = searchTerm || yearFilter !== 'all' || programFilter !== 'all' || typeFilter !== 'all';

  if (!summary || selectedFiles.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="bg-primary-50 p-6 rounded-full mb-6">
          <FileText className="h-12 w-12 text-primary-700" />
        </div>
        <h3 className="text-2xl font-medium text-neutral-800 mb-4">Generate Summary</h3>
        <p className="text-neutral-500 mb-8 text-center max-w-md">
          Select documents and create a comprehensive summary with citations to source material.
        </p>
        
        {/* Document Selection */}
        <div className="w-full max-w-md mb-6">
          <div className="relative" ref={searchRef}>
            <button
              onClick={() => setShowDocumentSelector(!showDocumentSelector)}
              className="w-full p-3 border border-neutral-300 rounded-lg text-left hover:bg-neutral-50 transition-colors"
            >
              {selectedFiles.length > 0 
                ? `${selectedFiles.length} document(s) selected`
                : 'Select documents to summarize'
              }
            </button>
            
            {/* Document Selector Dropdown */}
            {showDocumentSelector && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-neutral-200 rounded-lg shadow-lg z-50">
                <div className="p-4">
                  <h3 className="text-sm font-medium text-neutral-700 mb-3">Select Documents</h3>
                  
                  {/* Search Input */}
                  <div className="relative mb-3">
                    <input
                      type="text"
                      placeholder="Search documents..."
                      className="w-full pl-10 pr-12 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    <Search className="absolute left-3 top-2.5 h-5 w-5 text-neutral-400" />
                    <button
                      onClick={() => setShowFilters(!showFilters)}
                      className={`absolute right-3 top-2.5 h-5 w-5 transition-colors ${
                        hasActiveFilters ? 'text-primary-600' : 'text-neutral-400 hover:text-neutral-600'
                      }`}
                    >
                      <Filter />
                    </button>
                  </div>
                  
                  {/* Filter Panel */}
                  {showFilters && (
                    <div className="mb-3 p-3 bg-neutral-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-xs font-medium text-neutral-700">Filters</h4>
                        {hasActiveFilters && (
                          <button
                            onClick={clearAllFilters}
                            className="text-xs text-primary-600 hover:text-primary-700"
                          >
                            Clear all
                          </button>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <label className="block text-xs font-medium text-neutral-700 mb-1">Year</label>
                          <select
                            value={yearFilter}
                            onChange={(e) => setYearFilter(e.target.value)}
                            className="w-full p-1 text-xs border border-neutral-200 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                          >
                            <option value="all">All</option>
                            {years.map(year => (
                              <option key={year} value={year}>{year}</option>
                            ))}
                          </select>
                        </div>
                        
                        <div>
                          <label className="block text-xs font-medium text-neutral-700 mb-1">Program</label>
                          <select
                            value={programFilter}
                            onChange={(e) => setProgramFilter(e.target.value)}
                            className="w-full p-1 text-xs border border-neutral-200 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                          >
                            <option value="all">All</option>
                            {programs.map(program => (
                              <option key={program} value={program}>{program}</option>
                            ))}
                          </select>
                        </div>
                        
                        <div>
                          <label className="block text-xs font-medium text-neutral-700 mb-1">Type</label>
                          <select
                            value={typeFilter}
                            onChange={(e) => setTypeFilter(e.target.value)}
                            className="w-full p-1 text-xs border border-neutral-200 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                          >
                            <option value="all">All</option>
                            {types.map(type => (
                              <option key={type} value={type}>{type === 'final' ? 'Final Rule' : 'Proposed Rule'}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* File List */}
                  <div className="max-h-64 overflow-y-auto">
                    {filteredFiles.length > 0 ? (
                      <div className="space-y-2">
                        {filteredFiles.map((file) => (
                          <div
                            key={file.id}
                            className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                              selectedFiles.includes(file.id)
                                ? 'bg-primary-50 border border-primary-200'
                                : 'hover:bg-neutral-50'
                            }`}
                            onClick={() => handleFileSelect(file.id)}
                          >
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-neutral-800 truncate">{file.name}</p>
                              <div className="flex text-xs text-neutral-500 mt-1">
                                <span className="mr-2">{file.size}</span>
                                <span>{file.date}</span>
                              </div>
                            </div>
                            {selectedFiles.includes(file.id) && (
                              <div className="ml-2 w-2 h-2 bg-primary-600 rounded-full"></div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-4 text-center text-neutral-500 text-sm">
                        No documents found
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Selected Files Tags */}
          {selectedFiles.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {selectedFiles.map(fileId => {
                const file = files.find(f => f.id === fileId);
                if (!file) return null;
                
                return (
                  <div
                    key={fileId}
                    className="inline-flex items-center px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm"
                  >
                    <span className="truncate max-w-xs">{file.name}</span>
                    <button
                      onClick={() => removeSelectedFile(fileId)}
                      className="ml-2 hover:text-primary-900"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
        
        {selectedFiles.length > 0 && (
          <button 
            className="px-6 py-3 bg-primary-700 hover:bg-primary-800 text-white rounded-lg transition-colors flex items-center"
            onClick={handleGenerateSummary}
          >
            <RefreshCw className="h-5 w-5 mr-2" />
            Generate Summary
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b border-neutral-200 bg-white">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-semibold text-neutral-800">{summary.title}</h2>
            {selectedFiles.length > 0 && (
              <p className="text-sm text-neutral-500 mt-1">
                Based on: {selectedFileNames.join(', ')}
              </p>
            )}
          </div>
          <div className="flex space-x-2">
            <button 
              className="p-2 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
              title="Copy summary"
              onClick={handleCopySummary}
            >
              <Copy className="h-5 w-5" />
            </button>
            <button 
              className="p-2 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
              title="Download as markdown"
            >
              <Download className="h-5 w-5" />
            </button>
            <button 
              className="p-2 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
              title="Regenerate summary"
              onClick={handleGenerateSummary}
            >
              <RefreshCw className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {summary.sections.map((section) => (
            <div 
              key={section.id} 
              className="border border-neutral-200 rounded-lg overflow-hidden bg-white shadow-sm"
            >
              <div 
                className="flex items-center justify-between p-4 bg-neutral-50 cursor-pointer hover:bg-neutral-100 transition-colors"
                onClick={() => toggleSection(section.id)}
              >
                <h3 className="text-lg font-medium text-neutral-800">{section.title}</h3>
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
                <div className="p-4 bg-white">
                  <ul className="space-y-3">
                    {section.bullets.map((bullet) => (
                      <li key={bullet.id} className="flex items-start">
                        <span className="text-primary-500 mr-3 mt-1">•</span>
                        <div className="flex-1">
                          <span className="text-neutral-800 leading-relaxed">{bullet.content}</span>
                          <button 
                            className="ml-2 inline-flex items-center text-primary-600 hover:text-primary-700 text-sm font-medium hover:underline transition-colors"
                            onClick={() => handleCitationClick(bullet.citation)}
                          >
                            {bullet.citation}
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
=======
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
>>>>>>> dev
      </div>
    </div>
  );
};

export default SummaryTab;
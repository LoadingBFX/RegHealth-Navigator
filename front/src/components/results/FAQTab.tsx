import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/store';
import { RefreshCw, Download, Copy, HelpCircle, Search, Filter, X } from 'lucide-react';

const FAQTab: React.FC = () => {
  const { 
    faq, 
    setFAQ, 
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
  
  const handleGenerateFAQ = () => {
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
  };

  const handleCitationClick = (citationId: string) => {
    const citation = citations[citationId];
    if (citation) {
      setActiveCitation(citation);
      setShowCitationModal(true);
    }
  };

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

  if (!faq || selectedFiles.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="bg-primary-50 p-6 rounded-full mb-6">
          <HelpCircle className="h-12 w-12 text-primary-700" />
        </div>
        <h3 className="text-2xl font-medium text-neutral-800 mb-4">Generate FAQ</h3>
        <p className="text-neutral-500 mb-8 text-center max-w-md">
          Select documents and create frequently asked questions with detailed answers.
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
                : 'Select documents for FAQ'
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
            onClick={handleGenerateFAQ}
          >
            <RefreshCw className="h-5 w-5 mr-2" />
            Generate FAQ
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
            <h2 className="text-2xl font-semibold text-neutral-800">{faq.title}</h2>
            {selectedFiles.length > 0 && (
              <p className="text-sm text-neutral-500 mt-1">
                Based on: {selectedFileNames.join(', ')}
              </p>
            )}
          </div>
          <div className="flex space-x-2">
            <button 
              className="p-2 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
              title="Copy FAQ"
              onClick={handleCopyFAQ}
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
              title="Regenerate FAQ"
              onClick={handleGenerateFAQ}
            >
              <RefreshCw className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {faq.sections.map((section) => (
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
                  <div className="space-y-6">
                    {section.questions.map((qa, idx) => (
                      <div key={idx} className="border-l-4 border-primary-200 pl-4">
                        <h4 className="text-base font-medium text-neutral-800 mb-2">
                          Q: {qa.question}
                        </h4>
                        <div className="flex items-start">
                          <span className="text-neutral-500 mr-2 font-medium">A:</span>
                          <div className="flex-1">
                            <p className="text-neutral-700 leading-relaxed">{qa.answer}</p>
                            <button 
                              className="mt-2 inline-flex items-center text-primary-600 hover:text-primary-700 text-sm font-medium hover:underline transition-colors"
                              onClick={() => handleCitationClick(qa.citation)}
                            >
                              {qa.citation}
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FAQTab;
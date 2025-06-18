import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/store';
import { RefreshCw, Download, Copy, FileText, Search, Filter, X, AlertCircle } from 'lucide-react';
import { config } from '../../config';

interface Document {
  id: string;
  name: string;
  program: string;
  ruleType: string;
  sourceFile: string;
  title: string;
  year: string;
}

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
    setShowFilters,
  } = useStore();
  
  const [expandedSections, setExpandedSections] = useState<string[]>(['1']);
  const [showDocumentSelector, setShowDocumentSelector] = useState(false);
  const [availableDocuments, setAvailableDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const searchRef = useRef<HTMLDivElement>(null);
  const [hasGeneratedSummary, setHasGeneratedSummary] = useState(false);
  
  const programs = ['MPFS', 'HOSPICE', 'SNF', 'QPP'];
  const types = ['final', 'proposed'];
  const years = ['2024', '2023', '2022', '2021'];
  
  const selectedFileName = selectedFiles.length > 0 
    ? availableDocuments.find(file => file.id === selectedFiles[0])?.name || ''
    : '';
  
  // Filter files based on search and filters
  const filteredFiles = availableDocuments.filter(file => {
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
  
  // Fetch documents on mount
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await fetch(`${config.api.baseUrl}${config.api.endpoints.summarize.list}`);
        if (!response.ok) {
          throw new Error('Failed to fetch documents');
        }
        const data = await response.json();
        setAvailableDocuments(data.documents || []);
        setError(null);
      } catch (error) {
        console.error('Error fetching documents:', error);
        setError('Failed to fetch documents. Using sample data instead.');
        // Use sample data if fetch fails
        setAvailableDocuments(files.map(file => ({
          id: file.id,
          name: file.name,
          program: '',
          ruleType: '',
          sourceFile: file.name,
          title: file.name,
          year: ''
        })));
      }
    };
    
    fetchDocuments();
  }, []);
  
  const toggleSection = (sectionId: string) => {
    if (expandedSections.includes(sectionId)) {
      setExpandedSections(expandedSections.filter(id => id !== sectionId));
    } else {
      setExpandedSections([...expandedSections, sectionId]);
    }
  };
  
  const handleGenerateSummary = async () => {
    if (selectedFiles.length === 0) return;
    
    setIsLoading(true);
    setProcessing(true);
    setProcessingProgress(0);
    setError(null);
    
    try {
      const response = await fetch(`${config.api.baseUrl}${config.api.endpoints.summarize.generate}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_file: availableDocuments.find(doc => doc.id === selectedFiles[0])?.sourceFile
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate summary');
      }
      
      const data = await response.json();
      setSummary(data);
      setProcessingProgress(100);
      setHasGeneratedSummary(true);
    } catch (error) {
      console.error('Error generating summary:', error);
      setError('Failed to generate summary. Using sample data instead.');
      // Use sample summary from store if generation fails
      setSummary({
        title: '[sample]2024 MPFS Final Rule - Summary',
        sections: [
          {
            id: '1',
            title: '[sample]Payment Updates',
            bullets: [
              { id: '1.1', content: '[sample]Conversion factor updated to $32.75 for 2024', citation: '§1.1' },
              { id: '1.2', content: '[sample]New payment methodology for E/M services', citation: '§1.2' },
              { id: '1.3', content: '[sample]Updated practice expense calculations', citation: '§1.3' },
            ]
          },
          {
            id: '2',
            title: '[sample]Quality Measures',
            bullets: [
              { id: '2.1', content: '[sample]MIPS performance threshold increased to 82.5 points', citation: '§3.2' },
              { id: '2.2', content: '[sample]New quality measures for chronic care management', citation: '§3.3' },
              { id: '2.3', content: '[sample]Updated reporting requirements for telehealth services', citation: '§3.4' },
            ]
          },
          {
            id: '3',
            title: '[sample]Telehealth Provisions',
            bullets: [
              { id: '3.1', content: '[sample]Extended telehealth flexibilities through 2024', citation: '§4.1' },
              { id: '3.2', content: '[sample]New reimbursement rates for remote patient monitoring', citation: '§4.2' },
              { id: '3.3', content: '[sample]Updated geographic restrictions for telehealth services', citation: '§4.3' },
            ]
          }
        ]
      });
      setHasGeneratedSummary(true);
    } finally {
      setIsLoading(false);
      setProcessing(false);
    }
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
  };

  const handleCitationClick = (citationId: string) => {
    const citation = citations[citationId];
    if (citation) {
      setActiveCitation(citation);
      setShowCitationModal(true);
    }
  };

  const handleFileSelect = (fileId: string) => {
    // Only allow one file selection
    setSelectedFiles([fileId]);
    setShowDocumentSelector(false);
  };
  
  const removeSelectedFile = () => {
    setSelectedFiles([]);
  };
  
  const clearAllFilters = () => {
    setSearchTerm('');
    setYearFilter('all');
    setProgramFilter('all');
    setTypeFilter('all');
  };
  
  const hasActiveFilters = searchTerm || yearFilter !== 'all' || programFilter !== 'all' || typeFilter !== 'all';

  if (!summary || !hasGeneratedSummary) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="bg-primary-50 p-6 rounded-full mb-6">
          <FileText className="h-12 w-12 text-primary-700" />
        </div>
        <h3 className="text-2xl font-medium text-neutral-800 mb-4">Generate Summary</h3>
        <p className="text-neutral-500 mb-8 text-center max-w-md">
          Select a document to generate a comprehensive summary with citations to source material.
        </p>
        
        {/* Error Alert */}
        {error && (
          <div className="w-full max-w-md mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
            <AlertCircle className="h-5 w-5 text-red-500 mr-3 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
        
        {/* Document Selection */}
        <div className="w-full max-w-md mb-6">
          <div className="relative" ref={searchRef}>
            <button
              onClick={() => setShowDocumentSelector(!showDocumentSelector)}
              className="w-full p-3 border border-neutral-300 rounded-lg text-left hover:bg-neutral-50 transition-colors"
            >
              {selectedFiles.length > 0 
                ? selectedFileName
                : 'Select a document to summarize'
              }
            </button>
            
            {/* Document Selector Dropdown */}
            {showDocumentSelector && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-neutral-200 rounded-lg shadow-lg z-50">
                <div className="p-4">
                  <h3 className="text-sm font-medium text-neutral-700 mb-3">Select Document</h3>
                  
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
                                ? 'bg-primary-50 text-primary-700'
                                : 'hover:bg-neutral-50'
                            }`}
                            onClick={() => handleFileSelect(file.id)}
                          >
                            <span className="text-sm">{file.name}</span>
                            {selectedFiles.includes(file.id) && (
                              <div className="h-4 w-4 rounded-full bg-primary-600 flex items-center justify-center">
                                <div className="h-2 w-2 rounded-full bg-white" />
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-4 text-neutral-500">
                        No documents found
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Selected File */}
          {selectedFiles.length > 0 && (
            <div className="mt-4">
              <div className="flex items-center justify-between p-2 bg-neutral-50 rounded-lg">
                <span className="text-sm text-neutral-700">{selectedFileName}</span>
                <button
                  onClick={removeSelectedFile}
                  className="text-neutral-400 hover:text-neutral-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
          
          {/* Generate Button */}
          <button
            onClick={handleGenerateSummary}
            disabled={selectedFiles.length === 0 || isLoading}
            className={`w-full mt-4 p-3 rounded-lg transition-colors flex items-center justify-center ${
              selectedFiles.length === 0 || isLoading
                ? 'bg-neutral-300 text-neutral-500 cursor-not-allowed'
                : 'bg-primary-600 text-white hover:bg-primary-700'
            }`}
          >
            {isLoading ? (
              <>
                <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                Generating Summary...
              </>
            ) : (
              <>
                <RefreshCw className="h-5 w-5 mr-2" />
                Generate Summary
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-medium text-neutral-800">{summary.title}</h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopySummary}
            className="p-2 text-neutral-600 hover:text-neutral-800 transition-colors"
            title="Copy to clipboard"
          >
            <Copy className="h-5 w-5" />
          </button>
          <button
            onClick={() => {
              const element = document.createElement('a');
              const file = new Blob([JSON.stringify(summary, null, 2)], {type: 'application/json'});
              element.href = URL.createObjectURL(file);
              element.download = 'summary.json';
              document.body.appendChild(element);
              element.click();
              document.body.removeChild(element);
            }}
            className="p-2 text-neutral-600 hover:text-neutral-800 transition-colors"
            title="Download as JSON"
          >
            <Download className="h-5 w-5" />
          </button>
        </div>
      </div>
      
      <div className="space-y-6">
        {summary.sections.map(section => (
          <div key={section.id} className="bg-white rounded-lg border border-neutral-200">
            <button
              onClick={() => toggleSection(section.id)}
              className="w-full p-4 flex items-center justify-between text-left"
            >
              <h3 className="text-lg font-medium text-neutral-800">{section.title}</h3>
              <div className={`transform transition-transform ${
                expandedSections.includes(section.id) ? 'rotate-180' : ''
              }`}>
                <svg className="h-5 w-5 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </button>
            
            {expandedSections.includes(section.id) && (
              <div className="p-4 border-t border-neutral-200">
                <ul className="space-y-3">
                  {section.bullets.map(bullet => (
                    <li key={bullet.id} className="flex items-start">
                      <span className="flex-shrink-0 h-5 w-5 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs mr-3 mt-0.5">
                        •
                      </span>
                      <div>
                        <p className="text-neutral-700">{bullet.content}</p>
                        {bullet.citation && (
                          <button
                            onClick={() => handleCitationClick(bullet.citation)}
                            className="mt-1 text-sm text-primary-600 hover:text-primary-700"
                          >
                            {bullet.citation}
                          </button>
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
    </div>
  );
};

export default SummaryTab;
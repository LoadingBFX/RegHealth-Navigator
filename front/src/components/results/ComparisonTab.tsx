import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/store';
<<<<<<< HEAD
import { RefreshCw, GitCompare, Search, Filter, X } from 'lucide-react';

// Sample comparison data
const sampleComparison = {
  title: '2024 MPFS Final vs Proposed Rule Comparison',
  leftDocument: '2024_MPFS_proposed_2024-12345',
  rightDocument: '2024_MPFS_final_2024-14828',
  sections: [
    {
      title: 'Conversion Factor (§2.1)',
      changes: [
        {
          type: 'modified' as const,
          content: 'Conversion factor finalized at $32.75 for 2024',
          oldContent: 'Proposed conversion factor of $33.06 for 2024',
          section: 'left'
        },
        {
          type: 'added' as const,
          content: 'Additional budget neutrality adjustments applied based on public comments',
          section: 'right'
        }
      ]
    },
    {
      title: 'E/M Services Payment (§2.3)',
      changes: [
        {
          type: 'unchanged' as const,
          content: 'New payment methodology for evaluation and management services'
        },
        {
          type: 'modified' as const,
          content: 'Implementation timeline extended to allow for additional provider training',
          oldContent: 'Immediate implementation upon rule effective date',
          section: 'right'
        }
      ]
    },
    {
      title: 'MIPS Performance Threshold (§3.1)',
      changes: [
        {
          type: 'modified' as const,
          content: 'Performance threshold set at 82.5 points',
          oldContent: 'Proposed performance threshold of 85 points',
          section: 'left'
        },
        {
          type: 'added' as const,
          content: 'Hardship exception criteria expanded based on stakeholder feedback',
          section: 'right'
        }
      ]
    }
  ]
};

const ComparisonTab: React.FC = () => {
  const { 
    files, 
    selectedFiles, 
    setSelectedFiles,
    setProcessing, 
    setProcessingProgress, 
    comparison, 
    setComparison,
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
  
  const [expandedSections, setExpandedSections] = useState<string[]>([]);
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
  
  const toggleSection = (sectionTitle: string) => {
    if (expandedSections.includes(sectionTitle)) {
      setExpandedSections(expandedSections.filter(title => title !== sectionTitle));
    } else {
      setExpandedSections([...expandedSections, sectionTitle]);
    }
  };
  
  const handleGenerateComparison = () => {
    setProcessing(true);
    let progress = 0;
    
    const interval = setInterval(() => {
      progress += 5;
      setProcessingProgress(progress);
      
      if (progress >= 100) {
        clearInterval(interval);
        setProcessing(false);
        setProcessingProgress(0);
        setComparison(sampleComparison);
        setExpandedSections([sampleComparison.sections[0].title]);
      }
    }, 300);
  };
  
  const renderChangeIcon = (type: string) => {
    switch (type) {
      case 'added':
        return <div className="w-2 h-2 bg-success-500 rounded-full flex-shrink-0 mt-2" />;
      case 'removed':
        return <div className="w-2 h-2 bg-error-500 rounded-full flex-shrink-0 mt-2" />;
      case 'modified':
        return <div className="w-2 h-2 bg-warning-500 rounded-full flex-shrink-0 mt-2" />;
      default:
        return <div className="w-2 h-2 bg-neutral-300 rounded-full flex-shrink-0 mt-2" />;
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

  if (!comparison || selectedFiles.length < 2) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="bg-primary-50 p-6 rounded-full mb-6">
          <GitCompare className="h-12 w-12 text-primary-700" />
        </div>
        <h3 className="text-2xl font-medium text-neutral-800 mb-4">Compare Documents</h3>
        <p className="text-neutral-500 mb-8 text-center max-w-md">
          {selectedFiles.length < 2 
            ? 'Select at least two documents to compare and see what has changed between versions.' 
            : `Compare ${selectedFileNames.slice(0, 2).join(' and ')} to identify key differences.`}
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
                : 'Select documents to compare'
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
        
        {selectedFiles.length >= 2 && (
          <button 
            className="px-6 py-3 bg-primary-700 hover:bg-primary-800 text-white rounded-lg transition-colors flex items-center"
            onClick={handleGenerateComparison}
          >
            <GitCompare className="h-5 w-5 mr-2" />
            Generate Comparison
          </button>
        )}
      </div>
    );
  }
=======
import { SendHorizontal, GitCompare } from 'lucide-react';
import ChatMessage from '../chat/ChatMessage';

const ComparisonTab: React.FC = () => {
  const { 
    files,
    citations,
    setActiveCitation,
    setShowCitationModal,
    addMessage,
    clearMessages
  } = useStore();
  
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    {
      id: '1',
      role: 'user' as const,
      content: "What's the difference between 2024 MPFS final rule and 2024 MPFS proposed rule?"
    },
    {
      id: '2',
      role: 'assistant' as const,
      content: `Based on my analysis of the 2024 MPFS documents, here are the key differences between the proposed and final rules:

**Payment Updates:**
- **Proposed Rule**: Suggested conversion factor of $33.06 for 2024
- **Final Rule**: Finalized conversion factor at $32.75 for 2024 [§2.1]
- **Impact**: The final rule resulted in a lower conversion factor than initially proposed

**MIPS Performance Threshold:**
- **Proposed Rule**: Recommended performance threshold of 85 points
- **Final Rule**: Set performance threshold at 82.5 points [§3.1]
- **Rationale**: Reduced based on stakeholder feedback about implementation challenges

**E/M Services Payment:**
- **Proposed Rule**: Immediate implementation upon rule effective date
- **Final Rule**: Extended implementation timeline to allow for additional provider training [§2.3]
- **Benefit**: Gives healthcare providers more time to adapt to new requirements

**Telehealth Provisions:**
- **Proposed Rule**: Basic telehealth policy framework
- **Final Rule**: Expanded telehealth flexibilities through 2024 with new reimbursement rates for remote patient monitoring [§4.1]

**Stakeholder Input Integration:**
- The final rule incorporated over 2,000 public comments received during the comment period
- Added hardship exception criteria for MIPS based on stakeholder feedback [§3.2]
- Budget neutrality adjustments were applied based on public comments [§2.1]

**Key Takeaway**: The final rule generally became more provider-friendly compared to the proposed rule, with lower thresholds, extended timelines, and expanded flexibilities based on industry feedback.`,
      citations: ['§2.1', '§3.1', '§2.3', '§4.1', '§3.2']
    }
  ]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      // Add user message
      const userMessage = {
        id: Date.now().toString(),
        role: 'user' as const,
        content: input
      };
      
      setMessages(prev => [...prev, userMessage]);
      
      // Simulate assistant response for comparison
      setTimeout(() => {
        const comparisonResponses = [
          {
            content: `I've analyzed the differences between these documents. Here are the key changes:

**Major Policy Changes:**
- Payment methodology updates with revised conversion factors [§1.1]
- Quality measure modifications affecting MIPS scoring [§3.2]
- Telehealth policy expansions and new coverage areas [§4.1]

**Implementation Timeline Differences:**
- The final rule extended several implementation deadlines based on provider feedback
- New grace periods were added for certain quality reporting requirements [§3.3]

**Financial Impact:**
- Updated budget neutrality calculations resulted in different payment adjustments
- Regional variations in payment rates were modified [§2.2]

The analysis shows significant evolution from proposed to final rule based on stakeholder input.`,
            citations: ['§1.1', '§3.2', '§4.1', '§3.3', '§2.2']
          },
          {
            content: `Based on the document comparison, here are the primary differences:

**Regulatory Framework Changes:**
- Streamlined documentation requirements in the final version [§5.1]
- Simplified reporting procedures for smaller practices [§5.2]
- Enhanced compliance pathways with reduced administrative burden [§5.3]

**Coverage Expansions:**
- Additional services covered under the final rule
- Expanded eligibility criteria for certain programs [§6.1]
- New payment categories for emerging technologies [§6.2]

**Stakeholder Feedback Integration:**
- Over 1,500 comments were incorporated into the final rule
- Industry concerns about implementation costs were addressed [§7.1]

The final rule demonstrates significant responsiveness to public input while maintaining regulatory objectives.`,
            citations: ['§5.1', '§5.2', '§5.3', '§6.1', '§6.2', '§7.1']
          }
        ];
        
        const randomResponse = comparisonResponses[Math.floor(Math.random() * comparisonResponses.length)];
        
        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant' as const,
          content: randomResponse.content,
          citations: randomResponse.citations
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      }, 1000);
      
      setInput('');
    }
  };

  const handleCitationClick = (citationId: string) => {
    const citation = citations[citationId];
    if (citation) {
      setActiveCitation(citation);
      setShowCitationModal(true);
    }
  };
>>>>>>> dev

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
<<<<<<< HEAD
      <div className="p-6 border-b border-neutral-200 bg-white">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-semibold text-neutral-800">{comparison.title}</h2>
            <div className="flex items-center mt-2 text-sm text-neutral-500">
              <span className="px-2 py-1 bg-neutral-100 rounded mr-2">{comparison.leftDocument}</span>
              <span className="mx-2">vs</span>
              <span className="px-2 py-1 bg-neutral-100 rounded ml-2">{comparison.rightDocument}</span>
            </div>
          </div>
          <button 
            className="p-2 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
            title="Regenerate comparison"
            onClick={handleGenerateComparison}
          >
            <RefreshCw className="h-5 w-5" />
          </button>
        </div>
      </div>
      
      {/* Comparison Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="grid grid-cols-2 gap-px bg-neutral-200 h-full">
          {/* Left Document */}
          <div className="bg-white">
            <div className="p-4 bg-neutral-50 border-b border-neutral-200">
              <h3 className="font-medium text-neutral-800">{comparison.leftDocument}</h3>
              <p className="text-sm text-neutral-500">Proposed Rule</p>
            </div>
            <div className="p-4 space-y-4">
              {comparison.sections.map((section) => (
                <div key={section.title} className="border border-neutral-200 rounded-lg overflow-hidden">
                  <div 
                    className="p-3 bg-neutral-50 cursor-pointer flex items-center justify-between"
                    onClick={() => toggleSection(section.title)}
                  >
                    <h4 className="font-medium text-neutral-800">{section.title}</h4>
                    <svg 
                      className={`h-4 w-4 text-neutral-500 transition-transform ${
                        expandedSections.includes(section.title) ? 'transform rotate-180' : ''
                      }`} 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                  
                  {expandedSections.includes(section.title) && (
                    <div className="p-3 bg-white space-y-3">
                      {section.changes
                        .filter(change => change.section !== 'right')
                        .map((change, idx) => (
                        <div key={idx} className="flex items-start space-x-3">
                          {renderChangeIcon(change.type)}
                          <div className="flex-1">
                            {change.type === 'modified' && change.oldContent ? (
                              <p className="text-sm text-neutral-700">{change.oldContent}</p>
                            ) : (
                              <p className={`text-sm ${
                                change.type === 'added' 
                                  ? 'text-success-700 bg-success-50 p-2 rounded' 
                                  : change.type === 'removed' 
                                    ? 'text-error-700 bg-error-50 p-2 rounded line-through' 
                                    : change.type === 'modified' 
                                      ? 'text-warning-700 bg-warning-50 p-2 rounded' 
                                      : 'text-neutral-700'
                              }`}>
                                {change.content}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
          
          {/* Right Document */}
          <div className="bg-white">
            <div className="p-4 bg-neutral-50 border-b border-neutral-200">
              <h3 className="font-medium text-neutral-800">{comparison.rightDocument}</h3>
              <p className="text-sm text-neutral-500">Final Rule</p>
            </div>
            <div className="p-4 space-y-4">
              {comparison.sections.map((section) => (
                <div key={section.title} className="border border-neutral-200 rounded-lg overflow-hidden">
                  <div 
                    className="p-3 bg-neutral-50 cursor-pointer flex items-center justify-between"
                    onClick={() => toggleSection(section.title)}
                  >
                    <h4 className="font-medium text-neutral-800">{section.title}</h4>
                    <svg 
                      className={`h-4 w-4 text-neutral-500 transition-transform ${
                        expandedSections.includes(section.title) ? 'transform rotate-180' : ''
                      }`} 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                  
                  {expandedSections.includes(section.title) && (
                    <div className="p-3 bg-white space-y-3">
                      {section.changes
                        .filter(change => change.section !== 'left')
                        .map((change, idx) => (
                        <div key={idx} className="flex items-start space-x-3">
                          {renderChangeIcon(change.type)}
                          <div className="flex-1">
                            <p className={`text-sm ${
                              change.type === 'added' 
                                ? 'text-success-700 bg-success-50 p-2 rounded' 
                                : change.type === 'removed' 
                                  ? 'text-error-700 bg-error-50 p-2 rounded line-through' 
                                  : change.type === 'modified' 
                                    ? 'text-warning-700 bg-warning-50 p-2 rounded' 
                                    : 'text-neutral-700'
                            }`}>
                              {change.content}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
=======
      <div className="p-4 border-b border-neutral-200 bg-white">
        <div className="flex items-center">
          <GitCompare className="h-5 w-5 text-primary-600 mr-2" />
          <h2 className="text-lg font-medium text-neutral-800">Document Comparison</h2>
        </div>
        <p className="text-sm text-neutral-500 mt-1">
          Ask questions about differences between documents
        </p>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6">
            <div className="bg-primary-50 p-6 rounded-full mb-6">
              <GitCompare className="h-12 w-12 text-primary-700" />
            </div>
            <h3 className="text-xl font-medium text-neutral-800 mb-4">Compare Documents</h3>
            <p className="text-neutral-500 mb-6 max-w-md">
              Ask questions about differences between documents. For example, "What's the difference between 2024 MPFS final and proposed rules?"
            </p>
            <div className="space-y-3 w-full max-w-lg">
              {[
                "What's the difference between 2024 MPFS final and proposed rules?",
                "How do 2024 and 2023 MPFS payment rates compare?",
                "What changed between the proposed and final hospice rules?"
              ].map((suggestion, i) => (
                <button
                  key={i}
                  className="w-full text-left p-3 bg-neutral-100 hover:bg-neutral-200 rounded-lg text-sm text-neutral-700 transition-colors"
                  onClick={() => setInput(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage 
                key={message.id} 
                message={message}
                onCitationClick={handleCitationClick}
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
      {/* Input */}
      <div className="p-4 border-t border-neutral-200 bg-white">
        <form onSubmit={handleSubmit} className="flex items-center space-x-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about differences between documents..."
            className="flex-1 p-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className={`p-3 rounded-lg transition-colors ${
              input.trim()
                ? 'bg-primary-700 hover:bg-primary-800 text-white'
                : 'bg-neutral-200 text-neutral-400 cursor-not-allowed'
            }`}
          >
            <SendHorizontal className="h-5 w-5" />
          </button>
        </form>
>>>>>>> dev
      </div>
    </div>
  );
};

export default ComparisonTab;
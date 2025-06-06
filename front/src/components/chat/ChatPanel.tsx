import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/store';
import { SendHorizontal, RefreshCw, Plus, X, Search, Filter } from 'lucide-react';
import ChatMessage from './ChatMessage';

const ChatPanel: React.FC = () => {
  const { 
    messages, 
    addMessage, 
    clearMessages, 
    selectedFiles, 
    setSelectedFiles,
    files,
    showDocumentSelector,
    setShowDocumentSelector,
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
  
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
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
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowDocumentSelector(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [setShowDocumentSelector]);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      // Add user message
      addMessage({
        id: Date.now().toString(),
        role: 'user',
        content: input
      });
      
      // Simulate assistant response
      setTimeout(() => {
        const responses = [
          {
            content: `Based on the 2024 MPFS final rule, the conversion factor has been set at $32.75 [§1.1], representing a 3.4% decrease from 2023. This change affects payment calculations for all physician services [§1.2].`,
            citations: ['§1.1', '§1.2']
          },
          {
            content: `The new E/M payment methodology simplifies billing requirements [§2.1] and introduces time-based documentation options [§2.2]. Implementation begins January 1, 2024 [§2.3].`,
            citations: ['§2.1', '§2.2', '§2.3']
          },
          {
            content: `MIPS performance threshold for 2024 has been increased to 82.5 points [§3.1]. New quality measures focus on chronic care management [§3.2] and telehealth utilization [§3.3].`,
            citations: ['§3.1', '§3.2', '§3.3']
          }
        ];
        
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];
        
        addMessage({
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: randomResponse.content,
          citations: randomResponse.citations
        });
      }, 1000);
      
      setInput('');
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

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Chat Header */}
      <div className="p-4 border-b border-neutral-200 bg-white">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-medium text-neutral-800">Chat</h2>
            {selectedFiles.length > 0 && (
              <p className="text-sm text-neutral-500 mt-1">
                Analyzing: {selectedFileNames.join(', ')}
              </p>
            )}
          </div>
          <button 
            onClick={() => clearMessages()}
            className="p-2 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
            title="Clear conversation"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
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
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6">
            <div className="bg-primary-50 p-6 rounded-full mb-6">
              <svg className="h-12 w-12 text-primary-700\" fill="none\" stroke="currentColor\" viewBox="0 0 24 24">
                <path strokeLinecap="round\" strokeLinejoin="round\" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 className="text-xl font-medium text-neutral-800 mb-4">Start a conversation</h3>
            <p className="text-neutral-500 mb-6 max-w-md">
              Ask questions about regulatory documents. You can chat without selecting documents or choose specific files for targeted analysis.
            </p>
            <div className="space-y-3 w-full max-w-lg">
              {[
                "What are the key payment changes in the 2024 MPFS final rule?",
                "How do the new E/M documentation requirements work?",
                "What are the MIPS performance thresholds for 2024?"
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
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
      {/* Input */}
      <div className="p-4 border-t border-neutral-200 bg-white">
        <form onSubmit={handleSubmit} className="flex items-center space-x-3">
          <div className="relative" ref={searchRef}>
            <button
              type="button"
              onClick={() => setShowDocumentSelector(!showDocumentSelector)}
              className="p-3 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
              title="Select documents"
            >
              <Plus className="h-5 w-5" />
            </button>
            
            {/* Document Selector Dropdown */}
            {showDocumentSelector && (
              <div className="absolute bottom-full left-0 mb-2 w-96 bg-white border border-neutral-200 rounded-lg shadow-lg z-50">
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
                      type="button"
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
                            type="button"
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
          
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about the documents..."
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
      </div>
    </div>
  );
};

export default ChatPanel;
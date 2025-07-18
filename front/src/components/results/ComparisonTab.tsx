import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/store';
import { SendHorizontal, GitCompare, Loader2, AlertCircle } from 'lucide-react';
import ChatMessage from '../chat/ChatMessage';
import ComparisonResult from '../comparison/ComparisonResult';

const ComparisonTab: React.FC = () => {
  const { 
    files,
    citations,
    setActiveCitation,
    setShowCitationModal,
    addMessage,
    clearMessages,
    comparisonResult,
    isComparing,
    comparisonError,
    performComparison,
    setComparisonResult,
    setComparisonError
  } = useStore();
  
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    citations?: string[];
  }>>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isComparing) {
      const query = input.trim();
      setInput('');
      
      // Clear any previous error
      setComparisonError(null);
      
      // Add user message to chat
      const userMessage = {
        id: Date.now().toString(),
        role: 'user' as const,
        content: query
      };
      setMessages(prev => [...prev, userMessage]);
      
      try {
        // Perform the comparison
        await performComparison(query);
        
        // Add a success message to chat
        const successMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant' as const,
          content: `I've completed the comparison analysis for: "${query}". You can view the detailed results below, including section-by-section comparisons, unique sections, and an executive summary.`
        };
        setMessages(prev => [...prev, successMessage]);
      } catch (error) {
        // Add error message to chat
        const errorMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant' as const,
          content: `I encountered an error while performing the comparison: ${error instanceof Error ? error.message : 'Unknown error occurred'}. Please try again or refine your query.`
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    }
  };

  const handleCitationClick = (citationId: string) => {
    const citation = citations[citationId];
    if (citation) {
      setActiveCitation(citation);
      setShowCitationModal(true);
    }
  };

  const handleNewComparison = () => {
    setComparisonResult(null);
    setComparisonError(null);
    clearMessages();
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-neutral-200 bg-white">
        <div className="flex items-center">
          <div className="bg-yellow-100 p-2 rounded-lg mr-3">
            <GitCompare className="h-5 w-5 text-yellow-600" />
          </div>
          <h2 className="text-lg font-medium text-neutral-800">Document Comparison</h2>
        </div>
        <p className="text-sm text-neutral-500 mt-1">
          Ask questions about differences between documents
        </p>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {comparisonResult ? (
          // Show comparison results
          <div className="max-w-3xl mx-auto">
            <ComparisonResult result={comparisonResult} />
          </div>
        ) : (
          // Show chat interface
          <>
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center min-h-[400px] text-center px-4">
                <div className="bg-yellow-100 p-4 sm:p-6 rounded-full mb-4 sm:mb-6 shadow-lg border-2 border-yellow-200 flex items-center justify-center">
                  <GitCompare className="h-8 w-8 sm:h-12 sm:w-12 text-yellow-600" />
                </div>
                <h3 className="text-base sm:text-xl font-medium text-neutral-800 mb-2 sm:mb-4">Compare Documents</h3>
                <p className="text-neutral-500 mb-4 sm:mb-6 text-sm sm:text-base max-w-sm sm:max-w-md lg:max-w-lg">
                  Ask questions about differences between documents. For example, "What's the difference between 2024 MPFS final and proposed rules?"
                </p>
                <div className="space-y-2 sm:space-y-3 w-full max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg">
                  {[
                    "What's the difference between 2024 MPFS final and proposed rules?",
                    "How do 2024 and 2023 MPFS payment rates compare?",
                    "What changed between the proposed and final hospice rules?"
                  ].map((suggestion, i) => (
                    <button
                      key={i}
                      className="w-full text-left p-2 sm:p-3 bg-teal-100 hover:bg-teal-200 rounded-lg text-xs sm:text-sm text-teal-800 transition-colors"
                      onClick={() => setInput(suggestion)}
                      disabled={isComparing}
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
                
                {/* Loading indicator */}
                {isComparing && (
                  <div className="flex items-center justify-center p-6">
                    <div className="bg-white border rounded-lg p-4 flex items-center space-x-3">
                      <Loader2 className="h-5 w-5 text-primary-600 animate-spin" />
                      <span className="text-gray-600">Analyzing documents and comparing rules...</span>
                    </div>
                  </div>
                )}
                
                {/* Error display */}
                {comparisonError && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="h-5 w-5 text-red-600" />
                      <span className="text-red-700 font-medium">Comparison Error</span>
                    </div>
                    <p className="text-red-600 mt-2">{comparisonError}</p>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </>
            )}
          </>
        )}
      </div>
      
      {/* Input */}
      {!comparisonResult && (
        <div className="p-6">
          <div className="max-w-2xl mx-auto">
            <form onSubmit={handleSubmit} className="flex items-center space-x-3 bg-white rounded-2xl shadow-2xl p-2 border border-yellow-200">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={isComparing ? "Comparing documents..." : "Ask about differences between documents..."}
                disabled={isComparing}
                className="flex-1 px-6 py-4 border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-yellow-200 bg-transparent text-lg"
              />
              <button
                type="submit"
                disabled={!input.trim() || isComparing}
                className={`p-4 rounded-xl transition-all duration-200 ${
                  input.trim() && !isComparing
                    ? 'bg-gradient-to-r from-pink-400 to-pink-500 hover:from-pink-500 hover:to-pink-600 text-white shadow-lg hover:shadow-xl transform hover:scale-105'
                    : 'bg-pink-100 text-pink-300 cursor-not-allowed shadow-md'
                }`}
              >
                {isComparing ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  <SendHorizontal className="h-6 w-6" />
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComparisonTab;
import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/store';
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

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
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
      </div>
    </div>
  );
};

export default ComparisonTab;
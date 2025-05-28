import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/store';
import { SendHorizontal, RefreshCw } from 'lucide-react';
import ChatMessage from './ChatMessage';

const ChatPanel: React.FC = () => {
  const { messages, addMessage, clearMessages } = useStore();
  const [input, setInput] = useState('');
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
      addMessage({
        id: Date.now().toString(),
        role: 'user',
        content: input
      });
      
      // Simulate assistant response (would be API call in real app)
      setTimeout(() => {
        addMessage({
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `This is a simulated response to "${input}". In a real implementation, this would contain information extracted from the XML documents with proper citations.`,
          citations: ['§1.2', '§3.4']
        });
      }, 1000);
      
      setInput('');
    }
  };

  return (
    <div className="flex-1 flex flex-col border-r border-neutral-200 bg-white">
      <div className="p-3 border-b border-neutral-200 flex justify-between items-center">
        <h2 className="text-lg font-medium text-neutral-800">Chat</h2>
        <button 
          onClick={() => clearMessages()}
          className="p-1.5 text-neutral-500 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors"
          title="Reset conversation"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6">
            <div className="bg-primary-50 p-4 rounded-full mb-4">
              <svg className="h-8 w-8 text-primary-700\" fill="none\" stroke="currentColor\" viewBox="0 0 24 24\" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round\" strokeLinejoin="round\" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-neutral-800 mb-2">Start a conversation</h3>
            <p className="text-neutral-500 mb-4 max-w-md">
              Ask questions about the selected XML documents. All answers include citations to the source material.
            </p>
            <div className="space-y-2 w-full max-w-md">
              {[
                "What are the new safety requirements?",
                "Summarize the changes between these versions",
                "Extract all sections related to monitoring protocols"
              ].map((suggestion, i) => (
                <button
                  key={i}
                  className="w-full text-left p-2 bg-neutral-100 hover:bg-neutral-200 rounded-md text-sm text-neutral-700 transition-colors"
                  onClick={() => {
                    setInput(suggestion);
                  }}
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
      
      <div className="p-3 border-t border-neutral-200">
        <form onSubmit={handleSubmit} className="flex items-center space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about the XML documents..."
            className="flex-1 p-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className={`p-2 rounded-md ${
              input.trim()
                ? 'bg-primary-700 hover:bg-primary-800 text-white'
                : 'bg-neutral-200 text-neutral-400 cursor-not-allowed'
            } transition-colors`}
          >
            <SendHorizontal className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatPanel;
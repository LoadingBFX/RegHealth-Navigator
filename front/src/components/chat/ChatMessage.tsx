import React from 'react';
import { ExternalLink } from 'lucide-react';

interface ChatMessageProps {
  message: {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    citations?: string[];
  };
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  // Function to highlight citations in the message text
  const highlightCitations = (text: string, citations?: string[]) => {
    if (!citations || citations.length === 0) return text;
    
    let highlightedText = text;
    citations.forEach(citation => {
      const regex = new RegExp(`\\[${citation}\\]`, 'g');
      highlightedText = highlightedText.replace(
        regex,
        `<span class="inline-flex items-center text-primary-700 font-medium cursor-pointer hover:underline" data-citation="${citation}">[${citation}]</span>`
      );
    });
    
    return highlightedText;
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div 
        className={`max-w-3/4 rounded-lg p-3 ${
          isUser 
            ? 'bg-primary-700 text-white' 
            : 'bg-neutral-100 text-neutral-800'
        }`}
      >
        {isUser ? (
          <p className="text-sm">{message.content}</p>
        ) : (
          <>
            <div 
              className="text-sm"
              dangerouslySetInnerHTML={{ 
                __html: highlightCitations(message.content, message.citations) 
              }}
            />
            
            {message.citations && message.citations.length > 0 && (
              <div className="mt-2 pt-2 border-t border-neutral-200 text-xs text-neutral-500">
                <div className="flex items-center mb-1">
                  <ExternalLink className="h-3 w-3 mr-1" />
                  <span>Citations:</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {message.citations.map((citation, index) => (
                    <span 
                      key={index}
                      className="px-1.5 py-0.5 bg-neutral-200 text-neutral-700 rounded-md cursor-pointer hover:bg-primary-100 hover:text-primary-700 transition-colors"
                    >
                      {citation}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
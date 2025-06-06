import React from 'react';
import { useStore } from '../../store/store';

interface ChatMessageProps {
  message: {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    citations?: string[];
  };
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const { citations, setActiveCitation, setShowCitationModal } = useStore();
  const isUser = message.role === 'user';
  
  const handleCitationClick = (citationId: string) => {
    const citation = citations[citationId];
    if (citation) {
      setActiveCitation(citation);
      setShowCitationModal(true);
    }
  };
  
  // Function to highlight citations in the message text
  const renderContentWithCitations = (text: string, citationList?: string[]) => {
    if (!citationList || citationList.length === 0) return text;
    
    let parts = [text];
    
    citationList.forEach(citation => {
      const newParts: (string | JSX.Element)[] = [];
      
      parts.forEach((part, index) => {
        if (typeof part === 'string') {
          const regex = new RegExp(`\\[${citation.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]`, 'g');
          const splitParts = part.split(regex);
          
          for (let i = 0; i < splitParts.length; i++) {
            if (i > 0) {
              newParts.push(
                <button
                  key={`${index}-${i}-${citation}`}
                  onClick={() => handleCitationClick(citation)}
                  className="inline-flex items-center text-primary-700 font-medium cursor-pointer hover:underline hover:text-primary-800 transition-colors"
                >
                  [{citation}]
                </button>
              );
            }
            if (splitParts[i]) {
              newParts.push(splitParts[i]);
            }
          }
        } else {
          newParts.push(part);
        }
      });
      
      parts = newParts;
    });
    
    return parts;
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div 
        className={`max-w-3/4 rounded-lg p-4 ${
          isUser 
            ? 'bg-primary-700 text-white' 
            : 'bg-neutral-100 text-neutral-800'
        }`}
      >
        <div className="text-sm leading-relaxed">
          {renderContentWithCitations(message.content, message.citations)}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
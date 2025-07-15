import React from 'react';
<<<<<<< HEAD
import { useStore } from '../../store/store';

=======
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useStore } from '../../store/store';

interface SourceInfo {
  name: string;
  chunks: Array<{
    text: string;
    index: number;
  }>;
}

>>>>>>> dev
interface ChatMessageProps {
  message: {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    citations?: string[];
<<<<<<< HEAD
=======
    sources?: SourceInfo[];
>>>>>>> dev
  };
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
<<<<<<< HEAD
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
=======
  const { setActiveCitation, setShowCitationModal } = useStore();
  const isUser = message.role === 'user';
  
  const handleSourceClick = (source: SourceInfo) => {
    // Create citation-like object for the modal
    const citationData = {
      id: source.name,
      title: formatSourceName(source.name),
      content: source.chunks.map(chunk => chunk.text).join('\n\n...\n\n'),
      fullContent: source.chunks.map(chunk => chunk.text).join('\n\n...\n\n'),
      documentId: source.name,
      documentName: source.name
    };
    
    setActiveCitation(citationData);
    setShowCitationModal(true);
  };
  
  const formatSourceName = (filename: string): string => {
    if (!filename || !filename.endsWith('.xml')) {
      return filename;
    }
    
    const nameWithoutExt = filename.slice(0, -4);
    const parts = nameWithoutExt.split('_');
    
    if (parts.length >= 4) {
      const year = parts[0];
      const program = parts[1];
      const type = parts[2];
      const docId = parts[3];
      return `${year} ${program} ${type}, Doc id: ${docId}`;
    }
    return filename;
  };
  

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-3/4 rounded-lg p-4 bg-primary-700 text-white">
          <div className="text-sm leading-relaxed">
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  // For assistant messages, use provided sources from API
  const sources = message.sources || [];

  return (
    <div className="flex justify-start">
      <div className="max-w-3/4 rounded-lg p-4 bg-neutral-100 text-neutral-800 relative">
        {/* Demo indicator for sample data */}
        {message.content.includes('2024 MPFS final rule') || message.content.includes('conversion factor') ? (
          <div className="absolute -top-2 -right-2">
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
              Demo
            </span>
          </div>
        ) : null}
        <div className="text-sm leading-relaxed prose prose-sm max-w-none">
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              // Customize markdown rendering for better styling
              h1: ({children}) => <h1 className="text-lg font-semibold mb-2 text-neutral-800">{children}</h1>,
              h2: ({children}) => <h2 className="text-base font-semibold mb-2 text-neutral-800">{children}</h2>,
              h3: ({children}) => <h3 className="text-sm font-semibold mb-1 text-neutral-800">{children}</h3>,
              p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
              ul: ({children}) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
              ol: ({children}) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
              li: ({children}) => <li className="text-neutral-700">{children}</li>,
              strong: ({children}) => <strong className="font-semibold text-neutral-800">{children}</strong>,
              code: ({children}) => <code className="bg-neutral-200 px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
              blockquote: ({children}) => <blockquote className="border-l-4 border-neutral-300 pl-3 italic text-neutral-600">{children}</blockquote>
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        
        {sources.length > 0 && (
          <div className="mt-4 pt-3 border-t border-neutral-200">
            <div className="text-xs font-medium text-neutral-600 mb-2">Sources:</div>
            <div className="flex flex-wrap gap-2">
              {sources.map((source, index) => (
                <button
                  key={index}
                  onClick={() => handleSourceClick(source)}
                  className="inline-flex items-center px-2 py-1 bg-primary-50 text-primary-700 text-xs rounded-md hover:bg-primary-100 transition-colors border border-primary-200"
                >
                  {formatSourceName(source.name)}
                </button>
              ))}
            </div>
          </div>
        )}
>>>>>>> dev
      </div>
    </div>
  );
};

export default ChatMessage;
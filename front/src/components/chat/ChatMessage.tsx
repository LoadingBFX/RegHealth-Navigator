import React from 'react';
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

interface ChatMessageProps {
  message: {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    citations?: string[];
    sources?: SourceInfo[];
  };
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
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
      <div className="max-w-3/4 rounded-lg p-4 bg-neutral-100 text-neutral-800">
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
      </div>
    </div>
  );
};

export default ChatMessage;
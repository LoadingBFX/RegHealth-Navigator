import React from 'react';
import { useStore } from '../../store/store';
import { X, MessageSquare, Calendar, FileText } from 'lucide-react';

const HistoryModal: React.FC = () => {
  const { 
    showHistory, 
    setShowHistory, 
    history, 
    setMessages, 
    setSelectedFiles,
    setActiveTab,
    files 
  } = useStore();
  
  if (!showHistory) {
    return null;
  }
  
  const loadHistoryItem = (item: any) => {
    // Load the chat messages
    setMessages(item.messages);
    
    // Set selected files based on file names
    const fileIds = item.files.map((fileName: string) => {
      const file = files.find(f => f.name === fileName);
      return file?.id;
    }).filter(Boolean);
    setSelectedFiles(fileIds);
    
    // Switch to chat tab
    setActiveTab('chat');
    
    // Close modal
    setShowHistory(false);
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
        {/* Modal Header */}
        <div className="p-6 border-b border-neutral-200 flex items-center justify-between">
          <div className="flex items-center">
            <MessageSquare className="h-6 w-6 text-primary-600 mr-3" />
            <h3 className="text-xl font-semibold text-neutral-800">Chat History</h3>
          </div>
          <button
            onClick={() => setShowHistory(false)}
            className="p-2 text-neutral-400 hover:text-neutral-600 rounded-full hover:bg-neutral-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        {/* Modal Content */}
        <div className="flex-1 p-6 overflow-y-auto">
          {history.length === 0 ? (
            <div className="text-center py-12">
              <MessageSquare className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-neutral-600 mb-2">No Chat History</h4>
              <p className="text-neutral-500">Your chat conversations will appear here.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="border border-neutral-200 rounded-lg p-4 hover:bg-neutral-50 cursor-pointer transition-colors"
                  onClick={() => loadHistoryItem(item)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <h4 className="font-medium text-neutral-800">{item.name}</h4>
                    <div className="flex items-center text-sm text-neutral-500">
                      <Calendar className="h-4 w-4 mr-1" />
                      {item.date}
                    </div>
                  </div>
                  
                  <div className="flex items-center mb-3">
                    <FileText className="h-4 w-4 text-neutral-400 mr-2" />
                    <div className="flex flex-wrap gap-2">
                      {item.files.map((fileName, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-neutral-100 text-neutral-600 rounded text-xs"
                        >
                          {fileName}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div className="text-sm text-neutral-600">
                    <div className="flex items-center">
                      <MessageSquare className="h-3 w-3 mr-1" />
                      <span>{item.messages.length} messages</span>
                    </div>
                    {item.messages.length > 0 && (
                      <p className="mt-2 text-neutral-500 line-clamp-2">
                        {item.messages[0].content}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Modal Footer */}
        <div className="p-6 border-t border-neutral-200 bg-neutral-50">
          <div className="flex justify-end">
            <button
              onClick={() => setShowHistory(false)}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HistoryModal;
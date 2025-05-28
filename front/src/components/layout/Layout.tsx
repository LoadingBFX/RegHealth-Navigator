import React from 'react';
import Sidebar from './Sidebar';
import ChatPanel from '../chat/ChatPanel';
import ResultsPanel from '../results/ResultsPanel';
import Header from './Header';
import { useStore } from '../../store/store';

const Layout: React.FC = () => {
  const { isProcessing, processingProgress } = useStore();

  return (
    <div className="flex flex-col h-screen bg-neutral-50">
      <Header />
      
      {isProcessing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h3 className="text-xl font-semibold mb-4 text-primary-700">Processing XML Document</h3>
            <div className="w-full bg-neutral-200 rounded-full h-2.5 mb-4">
              <div 
                className="bg-primary-600 h-2.5 rounded-full transition-all duration-300 ease-in-out" 
                style={{ width: `${processingProgress}%` }}
              ></div>
            </div>
            <p className="text-sm text-neutral-600">
              {processingProgress < 100 
                ? `Processing large XML file (${processingProgress}%)...` 
                : 'Finalizing and caching results...'}
            </p>
          </div>
        </div>
      )}
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <ChatPanel />
        <ResultsPanel />
      </div>
    </div>
  );
};

export default Layout;
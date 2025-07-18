import React from 'react';
import ChatPanel from '../chat/ChatPanel';
import SummaryTab from '../results/SummaryTab';
import ComparisonTab from '../results/ComparisonTab';
import Header from './Header';
import HistoryModal from '../history/HistoryModal';
import CitationModal from '../citation/CitationModal';
import { useStore } from '../../store/store';
import { MessageSquare, FileText, GitCompare } from 'lucide-react';

const Layout: React.FC = () => {
  const { isProcessing, processingProgress, activeTab, setActiveTab } = useStore();

  const tabs = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'summary', label: 'Summary', icon: FileText },
    { id: 'compare', label: 'Compare', icon: GitCompare },
  ];

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatPanel />;
      case 'summary':
        return <SummaryTab />;
      case 'compare':
        return <ComparisonTab />;
      default:
        return <ChatPanel />;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-neutral-50">
      <Header />
      
      {isProcessing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-teal-50 p-6 rounded-lg shadow-lg max-w-md w-full border-2 border-teal-200">
            <h3 className="text-xl font-semibold mb-4 text-teal-700">Processing Document</h3>
            <div className="w-full bg-teal-100 rounded-full h-2.5 mb-4">
              <div 
                className="bg-teal-400 h-2.5 rounded-full transition-all duration-300 ease-in-out" 
                style={{ width: `${processingProgress}%` }}
              ></div>
            </div>
            <p className="text-sm text-teal-700">
              {processingProgress < 100 
                ? `Processing document (${processingProgress}%)...` 
                : 'Finalizing and caching results...'}
            </p>
          </div>
        </div>
      )}
      
      {/* Tab Navigation */}
      <div className="bg-white">
        <div className="flex space-x-1 px-4">
          {tabs.map((tab, idx) => {
            const Icon = tab.icon;
            // Assign pastel backgrounds for each tab for variety
            const pastelBg = [
              'bg-teal-100',
              'bg-pink-100',
              'bg-yellow-100'
            ];
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center px-4 py-3 text-sm font-medium border-b-2 transition-all rounded-xl relative z-10
                  ${activeTab === tab.id
                    ? `${pastelBg[idx]} text-neutral-800 shadow-lg scale-105 -translate-y-1 ${
                        idx === 0 ? 'border-teal-400' : 
                        idx === 1 ? 'border-pink-400' : 
                        'border-yellow-400'
                      }`
                    : 'bg-white border-transparent text-neutral-500 hover:shadow-md hover:text-neutral-700'}
                `}
                style={{ marginBottom: '-1px', transition: 'all 0.18s cubic-bezier(.4,2,.6,1)' }}
              >
                <Icon className="h-4 w-4 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
      
      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden">
        {renderActiveTab()}
      </div>
      
      {/* Modals */}
      <HistoryModal />
      <CitationModal />
    </div>
  );
};

export default Layout;
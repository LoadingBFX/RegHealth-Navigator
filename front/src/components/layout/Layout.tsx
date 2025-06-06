import React from 'react';
import ChatPanel from '../chat/ChatPanel';
import SummaryTab from '../results/SummaryTab';
import FAQTab from '../results/FAQTab';
import ComparisonTab from '../results/ComparisonTab';
import Header from './Header';
import HistoryModal from '../history/HistoryModal';
import CitationModal from '../citation/CitationModal';
import { useStore } from '../../store/store';
import { MessageSquare, FileText, HelpCircle, GitCompare } from 'lucide-react';

const Layout: React.FC = () => {
  const { isProcessing, processingProgress, activeTab, setActiveTab } = useStore();

  const tabs = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'summary', label: 'Summary', icon: FileText },
    { id: 'faq', label: 'FAQ', icon: HelpCircle },
    { id: 'compare', label: 'Compare', icon: GitCompare },
  ];

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatPanel />;
      case 'summary':
        return <SummaryTab />;
      case 'faq':
        return <FAQTab />;
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
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h3 className="text-xl font-semibold mb-4 text-primary-700">Processing Document</h3>
            <div className="w-full bg-neutral-200 rounded-full h-2.5 mb-4">
              <div 
                className="bg-primary-600 h-2.5 rounded-full transition-all duration-300 ease-in-out" 
                style={{ width: `${processingProgress}%` }}
              ></div>
            </div>
            <p className="text-sm text-neutral-600">
              {processingProgress < 100 
                ? `Processing document (${processingProgress}%)...` 
                : 'Finalizing and caching results...'}
            </p>
          </div>
        </div>
      )}
      
      {/* Tab Navigation */}
      <div className="bg-white border-b border-neutral-200">
        <div className="flex space-x-1 px-4">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
                }`}
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
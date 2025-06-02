import React from 'react';
import { useStore } from '../../store/store';
import SummaryTab from './SummaryTab';
import FAQTab from './FAQTab';
import ComparisonTab from './ComparisonTab';
import { ListChecks, GitBranch, DiffIcon } from 'lucide-react';

const ResultsPanel: React.FC = () => {
  const { activeTab, setActiveTab } = useStore();

  return (
    <div className="w-96 bg-white flex flex-col h-full">
      <div className="p-3 border-b border-neutral-200">
        <div className="flex space-x-1">
          <button
            className={`flex items-center py-1.5 px-3 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'summary'
                ? 'bg-primary-50 text-primary-700'
                : 'text-neutral-600 hover:text-primary-600 hover:bg-neutral-100'
            }`}
            onClick={() => setActiveTab('summary')}
          >
            <ListChecks className="h-4 w-4 mr-1.5" />
            Summary
          </button>
          <button
            className={`flex items-center py-1.5 px-3 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'faq'
                ? 'bg-primary-50 text-primary-700'
                : 'text-neutral-600 hover:text-primary-600 hover:bg-neutral-100'
            }`}
            onClick={() => setActiveTab('faq')}
          >
            <GitBranch className="h-4 w-4 mr-1.5" />
            FAQ
          </button>
          <button
            className={`flex items-center py-1.5 px-3 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'comparison'
                ? 'bg-primary-50 text-primary-700'
                : 'text-neutral-600 hover:text-primary-600 hover:bg-neutral-100'
            }`}
            onClick={() => setActiveTab('comparison')}
          >
            <DiffIcon className="h-4 w-4 mr-1.5" />
            Compare
          </button>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'summary' && <SummaryTab />}
        {activeTab === 'faq' && <FAQTab />}
        {activeTab === 'comparison' && <ComparisonTab />}
      </div>
    </div>
  );
};

export default ResultsPanel;
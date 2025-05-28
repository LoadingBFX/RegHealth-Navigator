import React from 'react';
import { useStore } from '../../store/store';
import { Layers, Settings, Share, BarChart2 } from 'lucide-react';

const Header: React.FC = () => {
  const { selectedFiles, files } = useStore();
  
  // Get the names of selected files
  const selectedFileNames = selectedFiles
    .map(id => files.find(file => file.id === id)?.name || '')
    .filter(Boolean);
  
  return (
    <header className="bg-white border-b border-neutral-200 shadow-nav">
      <div className="flex items-center justify-between px-4 py-2">
        <div className="flex items-center">
          <div className="flex items-center mr-4">
            <Layers className="h-6 w-6 text-primary-700 mr-2" />
            <h1 className="text-xl font-semibold text-primary-700">RegHealth</h1>
          </div>
          
          <div className="hidden md:flex items-center px-3 py-1 bg-neutral-100 rounded-md">
            <span className="text-sm text-neutral-500 mr-2">Active:</span>
            <span className="text-sm font-medium text-neutral-700 truncate max-w-md">
              {selectedFileNames.length > 0 
                ? selectedFileNames.join(', ') 
                : 'No files selected'}
            </span>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <button className="p-2 text-neutral-600 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors">
            <BarChart2 className="h-5 w-5" />
          </button>
          <button className="p-2 text-neutral-600 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors">
            <Share className="h-5 w-5" />
          </button>
          <button className="p-2 text-neutral-600 hover:text-primary-700 rounded-full hover:bg-neutral-100 transition-colors">
            <Settings className="h-5 w-5" />
          </button>
          <div className="ml-2 h-8 w-8 rounded-full bg-primary-700 text-white flex items-center justify-center">
            <span className="text-sm font-medium">RH</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
import React, { useState } from 'react';
import { useStore } from '../../store/store';
import { 
  // FolderOpen, 
  Clock, 
  Upload, 
  Search,
  Plus,
  FileText,
  CheckCircle
} from 'lucide-react';

const Sidebar: React.FC = () => {
  const { 
    activeSidebarTab, 
    setActiveSidebarTab, 
    files, 
    history, 
    selectedFiles, 
    setSelectedFiles 
  } = useStore();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [yearFilter, setYearFilter] = useState('all');
  const [programFilter, setProgramFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  const programs = ['MPFS', 'QPP', 'SNF', 'IPPS'];
  const types = ['Final Rule', 'Proposed Rule'];
  const years = ['2025', '2024', '2023', '2022'];

  const filteredFiles = files.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesYear = yearFilter === 'all' || file.date.includes(yearFilter);
    const matchesProgram = programFilter === 'all' || file.name.includes(programFilter);
    const matchesType = typeFilter === 'all' || (
      typeFilter === 'Final Rule' ? file.name.includes('Final') : 
      typeFilter === 'Proposed Rule' ? file.name.includes('Proposed') : 
      true
    );
    return matchesSearch && matchesYear && matchesProgram && matchesType;
  });

  const filteredHistory = history.filter(
    item => item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleFileSelect = (fileId: string) => {
    if (selectedFiles.includes(fileId)) {
      setSelectedFiles(selectedFiles.filter(id => id !== fileId));
    } else {
      setSelectedFiles([...selectedFiles, fileId]);
    }
  };

  return (
    <div className="w-64 border-r border-neutral-200 bg-white flex flex-col h-full">
      <div className="p-3 border-b border-neutral-200">
        <div className="flex space-x-1 bg-neutral-100 rounded-md p-1">
          <button
            className={`flex-1 py-1.5 px-3 rounded-sm text-sm font-medium transition-colors ${
              activeSidebarTab === 'files'
                ? 'bg-white text-primary-700 shadow-sm'
                : 'text-neutral-600 hover:text-primary-600'
            }`}
            onClick={() => setActiveSidebarTab('files')}
          >
            Files
          </button>
          <button
            className={`flex-1 py-1.5 px-3 rounded-sm text-sm font-medium transition-colors ${
              activeSidebarTab === 'history'
                ? 'bg-white text-primary-700 shadow-sm'
                : 'text-neutral-600 hover:text-primary-600'
            }`}
            onClick={() => setActiveSidebarTab('history')}
          >
            History
          </button>
        </div>
      </div>
      
      <div className="p-3 border-b border-neutral-200">
        <div className="relative mb-3">
          <input
            type="text"
            placeholder="Search..."
            className="w-full pl-8 pr-3 py-1.5 bg-neutral-100 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <Search className="absolute left-2.5 top-2 h-4 w-4 text-neutral-500" />
        </div>

        {activeSidebarTab === 'files' && (
          <div className="space-y-2">
            <select 
              className="w-full p-1.5 bg-white border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              value={yearFilter}
              onChange={(e) => setYearFilter(e.target.value)}
            >
              <option value="all">All Years</option>
              {years.map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>

            <select 
              className="w-full p-1.5 bg-white border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              value={programFilter}
              onChange={(e) => setProgramFilter(e.target.value)}
            >
              <option value="all">All Programs</option>
              {programs.map(program => (
                <option key={program} value={program}>{program}</option>
              ))}
            </select>

            <select 
              className="w-full p-1.5 bg-white border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="all">All Types</option>
              {types.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
        )}
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {activeSidebarTab === 'files' && (
          <div className="p-3">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-medium text-neutral-700">XML Documents</h3>
              <button className="text-primary-600 hover:text-primary-700 p-1 rounded-full hover:bg-neutral-100">
                <Upload className="h-4 w-4" />
              </button>
            </div>
            
            <ul className="space-y-2">
              {filteredFiles.map((file) => (
                <li 
                  key={file.id}
                  className={`px-3 py-2 rounded-md cursor-pointer transition-colors ${
                    selectedFiles.includes(file.id)
                      ? 'bg-primary-50 border border-primary-200'
                      : 'hover:bg-neutral-100'
                  }`}
                  onClick={() => handleFileSelect(file.id)}
                >
                  <div className="flex items-start">
                    <div className="mr-2 mt-0.5">
                      {selectedFiles.includes(file.id) ? (
                        <CheckCircle className="h-4 w-4 text-primary-600" />
                      ) : (
                        <FileText className="h-4 w-4 text-neutral-500" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-neutral-800 truncate">{file.name}</p>
                      <div className="flex text-xs text-neutral-500 mt-1">
                        <span className="mr-2">{file.size}</span>
                        <span>{file.date}</span>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {activeSidebarTab === 'history' && (
          <div className="p-3">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-medium text-neutral-700">Recent Sessions</h3>
              <button className="text-primary-600 hover:text-primary-700 p-1 rounded-full hover:bg-neutral-100">
                <Plus className="h-4 w-4" />
              </button>
            </div>
            
            <ul className="space-y-2">
              {filteredHistory.map((item) => (
                <li 
                  key={item.id}
                  className="px-3 py-2 rounded-md cursor-pointer hover:bg-neutral-100 transition-colors"
                >
                  <div className="flex items-start">
                    <div className="mr-2 mt-0.5">
                      <Clock className="h-4 w-4 text-neutral-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-neutral-800 truncate">{item.name}</p>
                      <div className="flex text-xs text-neutral-500 mt-1">
                        <span className="mr-2">{item.date}</span>
                        <span className="truncate">{item.files.join(', ')}</span>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      
      {/* <div className="p-3 border-t border-neutral-200">
        <button className="w-full flex items-center justify-center px-4 py-2 bg-primary-700 hover:bg-primary-800 text-white rounded-md transition-colors">
          <FolderOpen className="h-4 w-4 mr-2" />
          <span className="text-sm font-medium">Select XML Files</span>
        </button>
      </div> */}
    </div>
  );
};

export default Sidebar;
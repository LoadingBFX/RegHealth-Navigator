import { create } from 'zustand';
import config from '../config';
import { ComparisonResult, apiService } from '../services/api';

// Sample data with new naming convention
const sampleFiles = [
  { id: '1', name: '2024_MPFS_final_2024-14828', size: '156 MB', date: '2024-11-08' },
  { id: '2', name: '2024_MPFS_proposed_2024-12345', size: '187 MB', date: '2024-05-15' },
  { id: '3', name: '2024_HOSPICE_final_2024-15678', size: '92 MB', date: '2024-10-30' },
  { id: '4', name: '2023_SNF_final_2023-23456', size: '134 MB', date: '2023-11-15' },
];

const sampleHistory = [
  { 
    id: '1', 
    name: 'MPFS Payment Updates Analysis', 
    date: '2024-11-25', 
    files: ['2024_MPFS_final_2024-14828', '2024_MPFS_proposed_2024-12345'],
    messages: [
      { id: '1', role: 'user', content: 'What are the key changes in the 2024 MPFS final rule?' },
      { id: '2', role: 'assistant', content: 'The 2024 MPFS final rule includes several significant changes...', citations: ['§3.2', '§4.1'] }
    ]
  },
  { 
    id: '2', 
    name: 'Hospice Care Regulations Review', 
    date: '2024-11-22', 
    files: ['2024_HOSPICE_final_2024-15678'],
    messages: [
      { id: '1', role: 'user', content: 'What are the new hospice payment rates?' },
      { id: '2', role: 'assistant', content: 'The new hospice payment rates for 2024...', citations: ['§5.1'] }
    ]
  },
  { 
    id: '3', 
    name: 'SNF Quality Measures Discussion', 
    date: '2024-11-20', 
    files: ['2023_SNF_final_2023-23456'],
    messages: [
      { id: '1', role: 'user', content: 'How do the new quality measures affect SNF payments?' },
      { id: '2', role: 'assistant', content: 'The quality measures impact SNF payments through...', citations: ['§7.3', '§8.1'] }
    ]
  }
];

const sampleChat = [
  { 
    id: '1', 
    role: 'user', 
    content: 'What are the key changes in the 2024 MPFS final rule?' 
  },
  { 
    id: '2', 
    role: 'assistant', 
    content: 'The 2024 MPFS final rule includes several significant changes: enhanced monitoring protocols for adverse events [§3.2], expanded safety reporting timelines [§4.1], and additional risk assessment documentation [§6.3]. The conversion factor has been updated to reflect current economic conditions.',
    citations: ['§3.2', '§4.1', '§6.3'] 
  },
  {
    id: '3',
    role: 'user',
    content: 'Can you explain the new payment methodology for evaluation and management services?'
  },
  {
    id: '4',
    role: 'assistant',
    content: 'The new payment methodology introduces a simplified approach for E/M services [§2.1.4]. Key changes include: revised work RVUs for office visits [§2.1.5], updated practice expense calculations [§2.2.1], and new add-on codes for complex cases [§2.3.2].',
    citations: ['§2.1.4', '§2.1.5', '§2.2.1', '§2.3.2']
  }
];

const sampleSummary = {
  title: '2024 MPFS Final Rule - Summary',
  sections: [
    {
      id: '1',
      title: 'Payment Updates',
      bullets: [
        { id: '1.1', content: 'Conversion factor updated to $32.75 for 2024', citation: '§1.1' },
        { id: '1.2', content: 'New payment methodology for E/M services', citation: '§1.2' },
        { id: '1.3', content: 'Updated practice expense calculations', citation: '§1.3' },
      ]
    },
    {
      id: '2',
      title: 'Quality Measures',
      bullets: [
        { id: '2.1', content: 'MIPS performance threshold increased to 82.5 points', citation: '§3.2' },
        { id: '2.2', content: 'New quality measures for chronic care management', citation: '§3.3' },
        { id: '2.3', content: 'Updated reporting requirements for telehealth services', citation: '§3.4' },
      ]
    },
    {
      id: '3',
      title: 'Telehealth Provisions',
      bullets: [
        { id: '3.1', content: 'Extended telehealth flexibilities through 2024', citation: '§4.1' },
        { id: '3.2', content: 'New reimbursement rates for remote patient monitoring', citation: '§4.2' },
        { id: '3.3', content: 'Updated geographic restrictions for telehealth services', citation: '§4.3' },
      ]
    }
  ]
};



// Sample citations data
const sampleCitations = {
  '§1.1': {
    id: '§1.1',
    title: 'Conversion Factor Update',
    content: 'For CY 2024, we are finalizing a conversion factor of $32.75. This represents a decrease of 3.4 percent from the CY 2023 conversion factor of $33.89.',
    fullContent: 'For CY 2024, we are finalizing a conversion factor of $32.75. This represents a decrease of 3.4 percent from the CY 2023 conversion factor of $33.89. The decrease is primarily due to the expiration of the 0 percent update that was provided in CY 2023 under the Consolidated Appropriations Act, 2023. We note that this conversion factor reflects the statutory payment update of 0.25 percent for CY 2024, as well as the required budget neutrality adjustments for changes to the relative value units (RVUs) and other payment policy changes finalized in this rule.',
    documentId: '1',
    documentName: '2024_MPFS_final_2024-14828'
  },
  '§1.2': {
    id: '§1.2',
    title: 'E/M Payment Methodology',
    content: 'We are finalizing our proposal to implement a new payment methodology for evaluation and management (E/M) services that will simplify billing and reduce administrative burden...',
    fullContent: 'We are finalizing our proposal to implement a new payment methodology for evaluation and management (E/M) services that will simplify billing and reduce administrative burden while ensuring appropriate payment for the complexity of services provided. This new methodology will be based on medical decision making or time, allowing practitioners greater flexibility in documenting and billing for their services.',
    documentId: '1',
    documentName: '2024_MPFS_final_2024-14828'
  },
  '§2.1': {
    id: '§2.1',
    title: 'Payment Update Framework',
    content: 'The Medicare physician fee schedule payment amounts are updated annually based on the Medicare Economic Index (MEI) and other factors...',
    fullContent: 'The Medicare physician fee schedule payment amounts are updated annually based on the Medicare Economic Index (MEI) and other factors as specified in section 1848(d) of the Social Security Act. For CY 2024, the update is 0.25 percent, which reflects the current statutory framework for physician payment updates.',
    documentId: '1',
    documentName: '2024_MPFS_final_2024-14828'
  },
  '§3.2': {
    id: '§3.2',
    title: 'MIPS Performance Threshold',
    content: 'The MIPS performance threshold for the 2024 performance period is 82.5 points.',
    fullContent: 'The MIPS performance threshold for the 2024 performance period is 82.5 points. This represents an increase from the 2023 threshold of 75 points. Clinicians who score below this threshold will receive a negative payment adjustment, while those who score above will receive positive adjustments based on their performance.',
    documentId: '1',
    documentName: '2024_MPFS_final_2024-14828'
  }
};

type FileType = {
  id: string;
  name: string;
  size: string;
  date: string;
  program?: string;
  year?: string;
  type?: string;
};

type HistoryItem = {
  id: string;
  name: string;
  date: string;
  files: string[];
  messages: ChatMessage[];
};

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations?: string[];
};

type SummaryBullet = {
  id: string;
  content: string;
  citation: string;
};

type SummarySection = {
  id: string;
  title: string;
  bullets: SummaryBullet[];
};

type Summary = {
  title: string;
  sections: SummarySection[];
};



type Citation = {
  id: string;
  title: string;
  content: string;
  fullContent: string;
  documentId: string;
  documentName: string;
};

// Legacy comparison types (kept for backward compatibility)
type ComparisonChange = {
  type: 'added' | 'removed' | 'modified' | 'unchanged';
  content: string;
  oldContent?: string;
  section?: string;
};

type ComparisonSection = {
  title: string;
  changes: ComparisonChange[];
};

type Comparison = {
  title: string;
  leftDocument: string;
  rightDocument: string;
  sections: ComparisonSection[];
};

type StoreState = {
  isLoading: boolean;
  setLoading: (loading: boolean) => void;
  
  activeTab: string;
  setActiveTab: (tab: string) => void;
  
  files: FileType[];
  addFile: (file: FileType) => void;
  setFiles: (files: FileType[]) => void;
  fetchFiles: () => Promise<void>;
  
  history: HistoryItem[];
  addHistoryItem: (item: HistoryItem) => void;
  
  selectedFiles: string[];
  setSelectedFiles: (fileIds: string[]) => void;
  
  messages: ChatMessage[];
  addMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  clearMessages: () => void;
  
  summary: Summary | null;
  setSummary: (summary: Summary | null) => void;
  
  comparison: Comparison | null;
  setComparison: (comparison: Comparison | null) => void;
  
  // New comparison result from API
  comparisonResult: ComparisonResult | null;
  setComparisonResult: (result: ComparisonResult | null) => void;
  
  // Comparison loading states
  isComparing: boolean;
  setIsComparing: (comparing: boolean) => void;
  
  comparisonError: string | null;
  setComparisonError: (error: string | null) => void;
  
  // Comparison API method
  performComparison: (query: string) => Promise<void>;
  
  citations: Record<string, Citation>;
  setCitations: (citations: Record<string, Citation>) => void;
  
  activeCitation: Citation | null;
  setActiveCitation: (citation: Citation | null) => void;
  
  isProcessing: boolean;
  setProcessing: (processing: boolean) => void;
  
  processingProgress: number;
  setProcessingProgress: (progress: number) => void;
  
  // Search and filter state
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  
  yearFilter: string;
  setYearFilter: (year: string) => void;
  
  programFilter: string;
  setProgramFilter: (program: string) => void;
  
  typeFilter: string;
  setTypeFilter: (type: string) => void;
  
  showFilters: boolean;
  setShowFilters: (show: boolean) => void;
  
  // History modal
  showHistory: boolean;
  setShowHistory: (show: boolean) => void;
  
  // Citation modal
  showCitationModal: boolean;
  setShowCitationModal: (show: boolean) => void;
  
  // Document selection for chat
  showDocumentSelector: boolean;
  setShowDocumentSelector: (show: boolean) => void;
};

export const useStore = create<StoreState>((set, get) => ({
  // Loading state
  isLoading: false,
  setLoading: (loading) => set({ isLoading: loading }),

  // Active tab
  activeTab: 'chat',
  setActiveTab: (tab) => set({ activeTab: tab }),

  // Files management
  files: sampleFiles,
  addFile: (file) => set((state) => ({ files: [...state.files, file] })),
  setFiles: (files) => set({ files }),
  fetchFiles: async () => {
    try {
      set({ isLoading: true });
      const response = await fetch(`${config.api.baseUrl}${config.api.endpoints.documents}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.documents) {
        // Transform the API response to match our FileType format
        const transformedFiles = data.documents.map((doc: any) => ({
          id: doc.id,
          name: doc.name,
          size: doc.size,
          date: doc.date,
          program: doc.program,
          year: doc.year,
          type: doc.type
        }));
        
        set({ files: transformedFiles });
      }
    } catch (error) {
      console.error('Error fetching files:', error);
      // Keep using sample files if API fails
      console.log("Daisy's cat seems to have hidden our files! Seon, Sai, Sarvesh, Dhruv and Fanxing are looking for them...");
    } finally {
      set({ isLoading: false });
    }
  },

  // History management
  history: [],
  addHistoryItem: (item) => set((state) => ({ history: [...state.history, item] })),

  // Selected files for chat
  selectedFiles: [],
  setSelectedFiles: (fileIds) => set({ selectedFiles: fileIds }),

  // Chat messages
  messages: [],
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setMessages: (messages) => set({ messages }),
  clearMessages: () => set({ messages: [] }),

  // Summary
  summary: sampleSummary,
  setSummary: (summary) => set({ summary }),

  // Comparison
  comparison: null,
  setComparison: (comparison) => set({ comparison }),

  // New comparison result from API
  comparisonResult: null,
  setComparisonResult: (result) => set({ comparisonResult: result }),

  // Comparison loading states
  isComparing: false,
  setIsComparing: (comparing) => set({ isComparing: comparing }),

  comparisonError: null,
  setComparisonError: (error) => set({ comparisonError: error }),

  // Comparison API method
  performComparison: async (query: string) => {
    try {
      set({ isComparing: true, comparisonError: null, comparisonResult: null });
      const result = await apiService.compareRules(query);
      set({ comparisonResult: result });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      set({ comparisonError: `Daisy's cat interrupted our comparison! Seon, Sai, Sarvesh, Dhruv and Fanxing are trying to catch it. Error: ${errorMessage}` });
    } finally {
      set({ isComparing: false });
    }
  },

  // Citations
  citations: sampleCitations,
  setCitations: (citations) => set({ citations }),

  // Active citation
  activeCitation: null,
  setActiveCitation: (citation) => set({ activeCitation: citation }),

  // Processing state
  isProcessing: false,
  setProcessing: (processing) => set({ isProcessing: processing }),

  processingProgress: 0,
  setProcessingProgress: (progress) => set({ processingProgress: progress }),

  // Search and filter state
  searchTerm: '',
  setSearchTerm: (term) => set({ searchTerm: term }),

  yearFilter: 'all',
  setYearFilter: (year) => set({ yearFilter: year }),

  programFilter: 'all',
  setProgramFilter: (program) => set({ programFilter: program }),

  typeFilter: 'all',
  setTypeFilter: (type) => set({ typeFilter: type }),

  showFilters: false,
  setShowFilters: (show) => set({ showFilters: show }),

  // History modal
  showHistory: false,
  setShowHistory: (show) => set({ showHistory: show }),

  // Citation modal
  showCitationModal: false,
  setShowCitationModal: (show) => set({ showCitationModal: show }),

  // Document selector
  showDocumentSelector: false,
  setShowDocumentSelector: (show) => set({ showDocumentSelector: show }),
}));
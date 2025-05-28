import { create } from 'zustand';

// Sample data for demonstration
const sampleFiles = [
  { id: '1', name: 'FDA-Guidance-2025.xml', size: '156 MB', date: '2025-05-20' },
  { id: '2', name: 'EMA-Guidelines-v3.2.xml', size: '187 MB', date: '2025-05-15' },
  { id: '3', name: 'ICH-E6-R3.xml', size: '92 MB', date: '2025-04-30' },
];

const sampleHistory = [
  { id: '1', name: 'Dosage comparison', date: '2025-05-25', files: ['FDA-Guidance-2025.xml', 'EMA-Guidelines-v3.2.xml'] },
  { id: '2', name: 'Safety regulations', date: '2025-05-22', files: ['ICH-E6-R3.xml'] },
];

const sampleChat = [
  { 
    id: '1', 
    role: 'user', 
    content: 'What are the new safety requirements?' 
  },
  { 
    id: '2', 
    role: 'assistant', 
    content: 'The new safety requirements include enhanced monitoring protocols for adverse events [§3.2], expanded safety reporting timelines [§4.1], and additional risk assessment documentation [§6.3].',
    citations: ['§3.2', '§4.1', '§6.3'] 
  },
  {
    id: '3',
    role: 'user',
    content: 'What specific changes were made to the monitoring protocols?'
  },
  {
    id: '4',
    role: 'assistant',
    content: 'The monitoring protocols now require daily assessment of serious adverse events [§3.2.1] rather than the previous weekly review. Additionally, a new centralized electronic monitoring system must be implemented [§3.2.3] with automated alerts for threshold breaches.',
    citations: ['§3.2.1', '§3.2.3']
  }
];

const sampleSummary = {
  title: 'FDA Guidance 2025 - Summary',
  sections: [
    {
      id: '1',
      title: 'Introduction',
      bullets: [
        { id: '1.1', content: 'Purpose of the updated guidance', citation: '§1.1' },
        { id: '1.2', content: 'Scope and applicability to medical devices', citation: '§1.2' },
      ]
    },
    {
      id: '2',
      title: 'Safety Monitoring',
      bullets: [
        { id: '2.1', content: 'Enhanced requirements for real-time monitoring', citation: '§3.2' },
        { id: '2.2', content: 'New electronic reporting system specifications', citation: '§3.3' },
        { id: '2.3', content: 'Protocol for handling critical incidents', citation: '§3.4' },
      ]
    },
    {
      id: '3',
      title: 'Compliance Requirements',
      bullets: [
        { id: '3.1', content: 'Updated documentation standards', citation: '§4.1' },
        { id: '3.2', content: 'Certification process changes', citation: '§4.2' },
        { id: '3.3', content: 'Audit frequency and scope revisions', citation: '§4.3' },
      ]
    }
  ]
};

const sampleMindmap = {
  title: 'FDA Guidance 2025',
  children: [
    {
      name: 'Introduction',
      children: [
        { name: 'Purpose (§1.1)', id: '1.1' },
        { name: 'Scope (§1.2)', id: '1.2' },
        { name: 'Regulatory Background (§1.3)', id: '1.3' },
      ]
    },
    {
      name: 'Safety Monitoring',
      children: [
        { name: 'Enhanced Requirements (§3.2)', id: '3.2' },
        { name: 'Reporting System (§3.3)', id: '3.3' },
        { name: 'Critical Incidents (§3.4)', id: '3.4' },
      ]
    },
    {
      name: 'Compliance',
      children: [
        { name: 'Documentation (§4.1)', id: '4.1' },
        { name: 'Certification (§4.2)', id: '4.2' },
        { name: 'Audits (§4.3)', id: '4.3' },
      ]
    }
  ]
};

type FileType = {
  id: string;
  name: string;
  size: string;
  date: string;
};

type HistoryItem = {
  id: string;
  name: string;
  date: string;
  files: string[];
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

type MindmapNode = {
  name: string;
  id?: string;
  children?: MindmapNode[];
};

type Mindmap = {
  title: string;
  children: MindmapNode[];
};

type StoreState = {
  isLoading: boolean;
  setLoading: (loading: boolean) => void;
  
  activeTab: string;
  setActiveTab: (tab: string) => void;
  
  activeSidebarTab: string;
  setActiveSidebarTab: (tab: string) => void;
  
  files: FileType[];
  addFile: (file: FileType) => void;
  
  history: HistoryItem[];
  addHistoryItem: (item: HistoryItem) => void;
  
  selectedFiles: string[];
  setSelectedFiles: (fileIds: string[]) => void;
  
  messages: ChatMessage[];
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  
  summary: Summary | null;
  setSummary: (summary: Summary | null) => void;
  
  mindmap: Mindmap | null;
  setMindmap: (mindmap: Mindmap | null) => void;
  
  isProcessing: boolean;
  setProcessing: (processing: boolean) => void;
  
  processingProgress: number;
  setProcessingProgress: (progress: number) => void;
};

export const useStore = create<StoreState>((set) => ({
  isLoading: false,
  setLoading: (loading) => set({ isLoading: loading }),
  
  activeTab: 'summary',
  setActiveTab: (tab) => set({ activeTab: tab }),
  
  activeSidebarTab: 'files',
  setActiveSidebarTab: (tab) => set({ activeSidebarTab: tab }),
  
  files: sampleFiles,
  addFile: (file) => set((state) => ({ files: [...state.files, file] })),
  
  history: sampleHistory,
  addHistoryItem: (item) => set((state) => ({ history: [item, ...state.history] })),
  
  selectedFiles: ['1'],
  setSelectedFiles: (fileIds) => set({ selectedFiles: fileIds }),
  
  messages: sampleChat,
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  clearMessages: () => set({ messages: [] }),
  
  summary: sampleSummary,
  setSummary: (summary) => set({ summary }),
  
  mindmap: sampleMindmap,
  setMindmap: (mindmap) => set({ mindmap }),
  
  isProcessing: false,
  setProcessing: (processing) => set({ isProcessing: processing }),
  
  processingProgress: 0,
  setProcessingProgress: (progress) => set({ processingProgress: progress }),
}));
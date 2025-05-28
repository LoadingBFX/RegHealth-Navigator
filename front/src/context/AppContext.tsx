import React, { createContext, useContext, ReactNode } from 'react';
import { useStore } from '../store/store';

type AppContextType = {
  isLoading: boolean;
  setLoading: (loading: boolean) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeSidebarTab: string;
  setActiveSidebarTab: (tab: string) => void;
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const { 
    isLoading, 
    setLoading, 
    activeTab, 
    setActiveTab, 
    activeSidebarTab, 
    setActiveSidebarTab 
  } = useStore();

  return (
    <AppContext.Provider value={{ 
      isLoading, 
      setLoading, 
      activeTab, 
      setActiveTab, 
      activeSidebarTab, 
      setActiveSidebarTab 
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
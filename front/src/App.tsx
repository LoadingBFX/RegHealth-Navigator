import Layout from './components/layout/Layout';
import { AppProvider } from './context/AppContext';

function App() {
  return (
    <AppProvider>
      <Layout />
    </AppProvider>
  );
}

// Test: force deploy by changing this comment
export default App;
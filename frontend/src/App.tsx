import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ToastProvider } from './components/ui/toast';
import { PageLoading } from './components/ui/loading';
import AuthPage from './pages/auth';
import DashboardPage from './pages/index';
import AgentDirectoryPage from './pages/AgentDirectory';
import JobDetails from './pages/JobDetails';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <PageLoading text="Checking authentication..." />;
  }

  return user ? <>{children}</> : <Navigate to="/auth" replace />;
};

const AppContent: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return <PageLoading text="Initializing application..." />;
  }

  return (
    <Routes>
      <Route 
        path="/auth" 
        element={user ? <Navigate to="/" replace /> : <AuthPage />} 
      />
      <Route 
        path="/" 
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/job/:id" 
        element={
          <ProtectedRoute>
            <JobDetails />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/agent-directory" 
        element={
          <ProtectedRoute>
            <AgentDirectoryPage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="*" 
        element={<Navigate to="/" replace />} 
      />
    </Routes>
  );
};

function App() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
      <ToastProvider maxToasts={3}>
        <AuthProvider>
          <Router>
            <AppContent />
          </Router>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;

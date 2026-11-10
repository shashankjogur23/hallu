import React, { useState } from 'react';
import { Layout } from './components/Layout';
import type { PageId } from './components/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { VerifyPage } from './pages/VerifyPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { HistoryPage } from './pages/HistoryPage';
import { AboutPage } from './pages/AboutPage';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [verifyPrefill, setVerifyPrefill] = useState<{
    question?: string;
    answer?: string;
    context?: string;
  } | undefined>(undefined);

  const handleNavigate = (
    page: PageId,
    prefill?: { question: string; answer: string; context: string }
  ) => {
    if (prefill) {
      setVerifyPrefill(prefill);
    }
    setCurrentPage(page);
  };

  const handleUseDocumentInVerify = (extractedText: string) => {
    setVerifyPrefill({
      context: extractedText,
      question: '',
      answer: '',
    });
    setCurrentPage('verify');
  };

  return (
    <Layout currentPage={currentPage} onSelectPage={(page) => handleNavigate(page)}>
      {currentPage === 'dashboard' && (
        <DashboardPage onNavigate={handleNavigate} />
      )}
      {currentPage === 'verify' && (
        <VerifyPage initialData={verifyPrefill} />
      )}
      {currentPage === 'documents' && (
        <DocumentsPage onUseDocumentInVerify={handleUseDocumentInVerify} />
      )}
      {currentPage === 'history' && (
        <HistoryPage />
      )}
      {currentPage === 'about' && (
        <AboutPage />
      )}
    </Layout>
  );
};

export default App;

import React, { useState, useEffect } from 'react';
import { User, Brain, AlertTriangle, FileText, Activity, History, Upload, Search, List } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// --- TYPE DEFINITIONS ---
interface SummaryData {
  summary: string;
  idea?: string | null;
}

interface PatientDetails {
  id: string;
  patient_name: string;
  report_summary: string;
}

// ============================================================================
// --- REUSABLE COMPONENTS ---
// ============================================================================

const LoadingSpinner = ({ text }: { text: string }) => (
  <>
    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
    <span>{text}</span>
  </>
);


// ============================================================================
// --- 1. SEARCH PAGE COMPONENT ---
// ============================================================================
const SearchPage = ({ onPatientSelect, onPdfUpload, searchResults, onSearch }: { 
  onPatientSelect: (patient: PatientDetails) => void; 
  onPdfUpload: (file: File) => void;
  searchResults: PatientDetails[];
  onSearch: (query: string) => Promise<void>;
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    await onSearch(searchQuery);
    setIsSearching(false);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      onPdfUpload(event.target.files[0]);
      setIsModalOpen(false);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === "application/pdf") {
      onPdfUpload(droppedFile);
      setIsModalOpen(false);
    } else {
      alert("Please drop a PDF file.");
    }
  };

  return (
    <>
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl p-8 mb-8 border border-white/20">
        <div className="space-y-6">
          <div>
            <label className="flex items-center text-lg font-semibold text-gray-700 mb-3">
              <Search className="w-5 h-5 mr-2 text-blue-600" />
              Search for Patient
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 bg-white hover:border-blue-300 focus:border-blue-500"
              placeholder="Enter Patient ID, Name, or other details..."
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={isSearching}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-xl transition flex items-center justify-center space-x-2"
          >
            {isSearching ? <LoadingSpinner text="Searching..." /> : 'Search'}
          </button>
          <div className="text-center text-gray-500">OR</div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="w-full flex items-center justify-center gap-2 bg-gray-600 text-white px-4 py-3 rounded-xl shadow hover:bg-gray-700 transition"
          >
            <Upload size={18} />
            Upload PDF Directly
          </button>
        </div>
      </div>

      {searchResults.length > 0 && (
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 border border-white/20">
          <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center"><List className="mr-2"/>Search Results</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-100">
                <tr>
                  <th className="p-3">Patient ID</th>
                  <th className="p-3">Name</th>
                  <th className="p-3">Details</th>
                  <th className="p-3">Action</th>
                </tr>
              </thead>
              <tbody>
                {searchResults.map((patient) => (
                  <tr key={patient.id} className="border-b hover:bg-blue-50">
                    <td className="p-3 font-mono">{patient.id}</td>
                    <td className="p-3">{patient.patient_name}</td>
                    <td className="p-3">{patient.report_summary}</td>
                    <td className="p-3">
                      <button
                        onClick={() => onPatientSelect(patient)}
                        className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                      >
                        Select
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <AnimatePresence>
          {isModalOpen && (
            <motion.div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <motion.div className="bg-white rounded-2xl shadow-xl p-6 w-96" initial={{ scale: 0.9 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}>
                <h2 className="text-xl font-semibold text-center mb-4">Upload Medical PDF</h2>
                <div className="w-full flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-xl p-8 cursor-pointer" onDragOver={(e) => e.preventDefault()} onDrop={handleDrop}>
                  <input type="file" id="pdf-upload" accept="application/pdf" className="hidden" onChange={handleFileSelect}/>
                  <Upload size={28} /><span className="mt-2">Drop file here or click to browse</span>
                </div>
                <button onClick={() => setIsModalOpen(false)} className="mt-6 w-full bg-gray-200 text-gray-700 px-4 py-2 rounded-xl">Cancel</button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
    </>
  );
}


// ============================================================================
// --- 2. SUMMARY PAGE COMPONENT ---
// ============================================================================
const SummaryPage = ({ patient, initialPdfFile, onBackToSearch }: { 
  patient: PatientDetails | null; 
  initialPdfFile: File | null; 
  onBackToSearch: () => void; 
}) => {
  const [idea, setThoughts] = useState('');
  const [pdfFile, setPdfFile] = useState<File | null>(initialPdfFile);
  const [isGenerating, setIsGenerating] = useState(false);
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null);
  const [summaryHistory, setSummaryHistory] = useState<SummaryData[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState<SummaryData | null>(null);
  const API_URL = import.meta.env.VITE_API_URL;
  const [isMerging, setIsMerging] = useState(false);
  const [historyPatientId, setHistoryPatientId] = useState('');
  const [areButtonsEnabled, setAreButtonsEnabled] = useState(false);
  const [canAdd, setCanAdd] = useState(false);
  const [useSavedPdf, setUseSavedPdf] = useState(false);

  const patientId = patient?.id || '';

    const handleBackToSearch = async () => {
    // flush UI state
    setSummaryData(null);
    setPdfFile(null);
    setThoughts('');
    setIsGenerating(false);

    // inform backend to stop processing
    try {
      await fetch(`${API_URL}/stop`, { method: "POST" });
    } catch (err) {
      console.error("Stop request failed:", err);
    }

    // navigate back immediately
    onBackToSearch();
  };

  
  useEffect(() => {
    if (initialPdfFile) {
        generateSummary();
    }
    if(patientId) {
        setAreButtonsEnabled(true);
    }
  }, [initialPdfFile, patientId]);
  
  const validateForm = () => {
    if (!patientId && !pdfFile) {
        alert('A patient or a PDF file is required.');
        return false;
    }
    return true;
  };

  const loadHistory = async (pid?: string) => {
    const effectiveId = pid || historyPatientId || patientId;
    if (!effectiveId.trim()) return;
    try {
      const response = await fetch(`${API_URL}/load_history`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patientId: effectiveId }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Failed to load history");
      setSummaryHistory(result.history || []);
    } catch (err) {
      console.error("Load history error:", err);
    }
  };

  const updateSummary = async (method: "replace" | "merge" | "add") => {
    if (!patientId || !summaryData) return;
    try {
      const response = await fetch(`${API_URL}/update_summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patientId,
          idea: idea && idea.trim() !== "" ? idea : summaryData.idea,
          summary: summaryData.summary,
          method,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Update failed");

      const cleanSummary: SummaryData = {
        summary: result.summary,
        idea: result.idea ?? idea ?? summaryData.idea ?? null,
      };
      if (method === "replace" || method === "merge") {
        setSummaryData(cleanSummary);
      }
      if (method === "add") {
        setCanAdd(false);
      }
      await loadHistory(patientId);
      if (method === "replace") {
        setAreButtonsEnabled(false);
        setCanAdd(false);
      }
    } catch (err) {
      console.error(`${method} error:`, err);
    } finally {
      if (method === "merge") setIsMerging(false);
    }
  };

  const handleReplace = () => updateSummary("replace");
  const handleMerge = () => {
    setIsMerging(true);
    updateSummary("merge");
  };
  const handleAddVersion = () => updateSummary("add");

  const generateSummary = async () => {
    if (!validateForm()) return;
    setIsGenerating(true);
    try {
      let body: FormData | string;
      let headers: HeadersInit = {};
      if (pdfFile) {
        body = new FormData();
        if (patientId) body.append("patientId", patientId);
        body.append("idea", idea);
        body.append("pdf", pdfFile);
      } else {
        body = JSON.stringify({ patientId, idea, pdf: useSavedPdf });
        headers = { "Content-Type": "application/json" };
      }
      const response = await fetch(`${API_URL}/start_summarisation`, { method: "POST", headers, body });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Failed to generate summary");
      setSummaryData({ summary: result.summary, idea: result.idea ?? (idea.trim() ? idea : null) });
      setCanAdd(true);
    } catch (err) {
      console.error("Generate error:", err);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <>
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl p-8 mb-8 border border-white/20">
        <div className="space-y-6">
          {patient && (
            <div className='p-4 bg-blue-100 border-l-4 border-blue-500 rounded-r-lg'>
                <p className='text-gray-600 text-sm'>Selected Patient</p>
                <p className='text-lg font-semibold text-gray-800'>{patient.patient_name} ({patient.id})</p>
            </div>
          )}
          {pdfFile && (
              <div className='p-4 bg-green-100 border-l-4 border-green-500 rounded-r-lg'>
                <p className='text-gray-600 text-sm'>Uploaded PDF</p>
                <p className="mt-1 text-green-800 font-medium">{pdfFile.name}</p>
              </div>
          )}
          
          {!pdfFile && patient && (
            <>
              <div className="flex items-center justify-between pt-4">
                <label htmlFor="useSavedPdf" className="text-lg font-semibold text-gray-700">Use saved PDF from DB</label>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" id="useSavedPdf" className="sr-only peer" checked={useSavedPdf} onChange={(e) => setUseSavedPdf(e.target.checked)}/>
                  <div className="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
                </label>
              </div>
              <div>
                <label className="flex items-center text-lg font-semibold text-gray-700 mb-3"><FileText className="w-5 h-5 mr-2" />Your Thoughts</label>
                <textarea value={idea} onChange={(e) => setThoughts(e.target.value)} rows={4} className="w-full p-3 rounded-xl border-2" placeholder="Add clinical notes..."/>
              </div>
            </>
          )}

          <button
            onClick={generateSummary}
            disabled={isGenerating || summaryData !== null}
            className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 disabled:from-gray-400 text-white font-semibold py-4 rounded-xl flex items-center justify-center space-x-2"
          >
            {isGenerating ? <LoadingSpinner text="Generating..." /> : (
              <><Brain className="w-5 h-5" /><span>Generate AI Summary</span></>
            )}
          </button>
        </div>
      </div>
      
      {summaryData && (
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 border border-white/20 animate-in slide-in-from-bottom duration-700">
            <div className="flex items-center mb-6">
              <Activity className="w-8 h-8 text-blue-600 mr-3" />
              <h2 className="text-2xl font-bold text-gray-800">AI Generated Summary</h2>
            </div>
            <div className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl p-6 border-l-4 border-blue-500">
              <p className="text-gray-700 leading-relaxed text-lg">{summaryData.summary}</p>
            </div>
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={handleReplace}
                disabled={!areButtonsEnabled}
                className={`px-6 py-3 rounded-lg font-medium transition ${!areButtonsEnabled ? 'bg-gray-400 cursor-not-allowed text-gray-200' : 'bg-red-600 text-white hover:bg-red-700'}`}
              >
                Replace
              </button>
              <button
                onClick={handleMerge}
                disabled={!areButtonsEnabled || isMerging}
                className={`px-6 py-3 rounded-lg font-medium transition flex items-center justify-center space-x-2 ${
                  !areButtonsEnabled || isMerging
                    ? 'bg-gray-400 cursor-not-allowed text-gray-200'
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
              >
                {isMerging ? <LoadingSpinner text="Merging..." /> : <span>Merge</span>}
              </button>

              <button
                onClick={handleAddVersion}
                disabled={!areButtonsEnabled || !canAdd}
                className={`px-6 py-3 rounded-lg font-medium transition ${
                  !areButtonsEnabled || !canAdd
                    ? 'bg-gray-400 cursor-not-allowed text-gray-200'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                Add This Version
              </button>
            </div>
          </div>
      )}

      <div className="fixed bottom-6 left-6">
          <button onClick={handleBackToSearch} className="px-4 py-2 rounded-lg shadow bg-gray-600 text-white hover:bg-gray-700">
            Back to Search
          </button>
      </div>

      {/* History and Full Summary Modals are here */}
    </>
  );
}


// ============================================================================
// --- 3. MAIN APP COMPONENT ---
// ============================================================================
function App() {
  const [view, setView] = useState<'search' | 'summary'>('search');
  const [patientDetails, setPatientDetails] = useState<PatientDetails[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<PatientDetails | null>(null);
  const [uploadedPdf, setUploadedPdf] = useState<File | null>(null);
  const API_URL = import.meta.env.VITE_API_URL;

  const handleSearch = async (query: string) => {
    try {
      const response = await fetch(`${API_URL}/searchpatient`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      if (!response.ok) throw new Error('Search failed');
      const data = await response.json();
      setPatientDetails(data.patients || []);
    } catch (error) {
      console.error("Search error:", error);
      setPatientDetails([]);
    }
  };

  const handlePatientSelect = (patient: PatientDetails) => {
    setSelectedPatient(patient);
    setUploadedPdf(null);
    setView('summary');
  };
  
  const handlePdfUpload = (file: File) => {
    setUploadedPdf(file);
    setSelectedPatient(null);
    setView('summary');
  }

  const handleBackToSearch = () => {
    setView('search');
    setSelectedPatient(null);
    setUploadedPdf(null);
    setPatientDetails([]);
  };

  return (
    <div className="min-h-screen bg-cover bg-center relative" style={{ backgroundImage: `url('https://www.sparrc.com/wp-content/uploads/2023/08/abt-us.jpg')`, backgroundAttachment: 'fixed' }}>
      <div className="absolute inset-0 bg-white opacity-70"></div>
      <div className="container mx-auto px-4 py-8 max-w-4xl relative z-10">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <img src="https://www.sparrc.com/wp-content/uploads/2023/08/logo.png" alt="MediSummary AI Logo" className="h-12 mr-3" />
            <h1 className="text-4xl font-bold text-gray-800">MediSummary AI</h1>
          </div>
        </div>

        {view === 'search' && <SearchPage onPatientSelect={handlePatientSelect} onPdfUpload={handlePdfUpload} searchResults={patientDetails} onSearch={handleSearch} />}
        {view === 'summary' && <SummaryPage patient={selectedPatient} initialPdfFile={uploadedPdf} onBackToSearch={handleBackToSearch} />}
        
        <div className="text-center mt-12 text-gray-500">
          <p>© 2025 MediSummary AI</p>
        </div>
      </div>
    </div>
  );
}

export default App;
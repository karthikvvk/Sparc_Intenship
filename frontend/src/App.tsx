import React, { useState, useEffect, useRef } from 'react';
import { User, Brain, AlertTriangle, FileText, Activity, History, Upload, Search, List, X, BarChart2, BookOpen } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// --- TYPE DEFINITIONS ---
interface SummaryData {
  summary: string;
  idea?: string | null;
}

// A simple type for prediction data for now
interface PredictionData {
    prediction: string;
    confidence?: number;
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

// Helper: parse tag-based summary strings with <heading> and <point> per-line


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
  const fileInputRef = useRef<HTMLInputElement>(null);

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
  
  const handleAreaClick = () => {
    fileInputRef.current?.click();
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
          <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center"><List className="mr-2" />Search Results</h2>
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
              <div
                className="w-full flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-xl p-8 cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition"
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={handleAreaClick}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  id="pdf-upload"
                  accept="application/pdf"
                  className="hidden"
                  onChange={handleFileSelect}
                />
                <Upload size={28} className="text-gray-500" />
                <span className="mt-2 text-gray-600">Drop file here or click to browse</span>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="mt-6 w-full bg-gray-200 text-gray-700 px-4 py-2 rounded-xl hover:bg-gray-300">Cancel</button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}


// ============================================================================
// --- 2. SUMMARY & PREDICTION PAGE COMPONENT ---
// ============================================================================
const ActionPage = ({
  patient,
  initialPdfFile,
  onBackToSearch,
  activeTab,
  isGeneratingSummary,
  setIsGeneratingSummary,
  isGeneratingPrediction,
  setIsGeneratingPrediction,
}: {
  patient: PatientDetails | null;
  initialPdfFile: File | null;
  onBackToSearch: () => void;
  activeTab: 'summary' | 'prediction';
  isGeneratingSummary: boolean;
  setIsGeneratingSummary: (isGenerating: boolean) => void;
  isGeneratingPrediction: boolean;
  setIsGeneratingPrediction: (isGenerating: boolean) => void;
}) => {
  const [idea, setThoughts] = useState('');
  const [pdfFile, setPdfFile] = useState<File | null>(initialPdfFile);
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null);
  const [predictionData, setPredictionData] = useState<PredictionData | null>(null); // State for prediction result
  const [summaryHistory, setSummaryHistory] = useState<SummaryData[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState<SummaryData | null>(null);
  // const API_URL = import.meta.env.VITE_API_URL;
  const [API_URL, setAPI_URL] = useState("");

  useEffect(() => {
    async function loadApiUrl() {
      const res = await fetch("/bk.json");
      const text = await res.text();
      const parts = text.trim().split("=");

      if (parts.length === 2) {
        setAPI_URL(parts[1].trim());
      }
    }

    loadApiUrl();
  }, []);
  const [isMerging, setIsMerging] = useState(false);
  const [historyPatientId, setHistoryPatientId] = useState('');
  const [areButtonsEnabled, setAreButtonsEnabled] = useState(false);
  const [canAdd, setCanAdd] = useState(false);
  const [useSavedPdf, setUseSavedPdf] = useState(false);
  const changePdfInputRef = useRef<HTMLInputElement>(null);

  const patientId = patient?.id || '';
  
  useEffect(() => {
    if (patientId) {
      setHistoryPatientId(patientId);
      setAreButtonsEnabled(true);
      loadHistory(patientId);
    }
  }, [patientId]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
        setPdfFile(event.target.files[0]);
        setSummaryData(null);
        setPredictionData(null); // Reset prediction data as well
        setAreButtonsEnabled(false);
        setCanAdd(false);
    }
  };
  
  const validateForm = () => {
    if (!patientId && !pdfFile) {
        alert('A patient or a PDF file is required.');
        return false;
    }
    return true;
  };

  const loadHistory = async (pid: string) => {
    if (!pid.trim()) return;
    try {
      const response = await fetch(`${API_URL}/load_history`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patientId: pid }),
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
    setIsMerging(method === "merge");
    try {
      const response = await fetch(`${API_URL}/update_summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patientId,
          idea: idea.trim() ? idea : summaryData.idea,
          summary: summaryData.summary,
          method,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Update failed");
      await loadHistory(patientId);
      if (method !== "add") {
        setSummaryData({ summary: result.summary, idea: result.idea ?? idea ?? summaryData.idea ?? null });
      }
      if (method === "add" || method === "replace") {
        setCanAdd(false);
      }
      if (method === "replace") setAreButtonsEnabled(false);
    } catch (err) {
      console.error(`${method} error:`, err);
    } finally {
      setIsMerging(false);
    }
  };

  const handleGenerate = async () => {
    if (!validateForm()) return;
    
    if (activeTab === 'summary') {
      await generateSummary();
    } else {
      await generatePrediction();
    }
  };
  
  const generateSummary = async () => {
    setIsGeneratingSummary(true);
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
      console.error("Generate summary error:", err);
    } finally {
      setIsGeneratingSummary(false);
    }
  };
  
  const generatePrediction = async () => {
    setIsGeneratingPrediction(true);
    // This is a placeholder for the actual prediction API call
    try {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate network delay
        setPredictionData({
            prediction: "Based on the provided data, there is a moderate risk of developing Type 2 Diabetes within the next 5 years.",
            confidence: 0.75
        });
    } catch(err) {
        console.error("Generate prediction error:", err);
    } finally {
        setIsGeneratingPrediction(false);
    }
  };

  const isGenerating = isGeneratingSummary || isGeneratingPrediction;
  
  // Determine button state based on the active tab
  const isButtonDisabled = activeTab === 'summary' 
    ? isGeneratingSummary || summaryData !== null
    : isGeneratingPrediction || predictionData !== null;
    
  const buttonText = activeTab === 'summary' 
    ? (isGeneratingSummary ? 'Generating Summary...' : 'Generate AI Summary')
    : (isGeneratingPrediction ? 'Generating Prediction...' : 'Generate AI Prediction');

  const ButtonIcon = activeTab === 'summary' ? Brain : BarChart2;

  return (
    <>
      <div className="fixed top-6 right-6 z-20">
        <button
          onClick={() => setShowHistory(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-xl shadow-lg hover:bg-blue-700 transition transform hover:scale-105"
        >
          <History className="w-5 h-5" />
          <span>View History</span>
        </button>
      </div>

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl p-8 mb-8 border border-white/20">
        <div className="space-y-6">
          {patient && (
            <div className='p-4 bg-blue-100 border-l-4 border-blue-500 rounded-r-lg'>
              <p className='text-gray-600 text-sm'>Selected Patient</p>
              <p className='text-lg font-semibold text-gray-800'>{patient.patient_name} ({patient.id})</p>
            </div>
          )}
          {pdfFile && (
            <div className='p-4 bg-green-100 border-l-4 border-green-500 rounded-r-lg flex items-center justify-between'>
              <div>
                <p className='text-gray-600 text-sm'>Uploaded PDF</p>
                <p className="mt-1 text-green-800 font-medium">{pdfFile.name}</p>
              </div>
              <button
                onClick={() => changePdfInputRef.current?.click()}
                className="bg-green-600 text-white text-sm px-3 py-1 rounded-lg hover:bg-green-700 transition"
              >
                Change PDF
              </button>
              <input type="file" ref={changePdfInputRef} onChange={handleFileChange} accept="application/pdf" className="hidden"/>
            </div>
          )}
          {!pdfFile && patient && (
            <div className="flex items-center justify-between pt-4">
              <label htmlFor="useSavedPdf" className="text-lg font-semibold text-gray-700">Use saved PDF from DB</label>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" id="useSavedPdf" className="sr-only peer" checked={useSavedPdf} onChange={(e) => setUseSavedPdf(e.target.checked)}/>
                <div className="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
              </label>
            </div>
          )}
          <div>
            <label className="flex items-center text-lg font-semibold text-gray-700 mb-3"><FileText className="w-5 h-5 mr-2" />Your Thoughts</label>
            <textarea value={idea} onChange={(e) => setThoughts(e.target.value)} rows={4} className="w-full p-3 rounded-xl border-2" placeholder="Add clinical notes..."/>
          </div>
          <button
            onClick={handleGenerate}
            disabled={isButtonDisabled}
            className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 disabled:from-gray-400 text-white font-semibold py-4 rounded-xl flex items-center justify-center space-x-2"
          >
            {isGenerating ? <LoadingSpinner text={buttonText} /> : <><ButtonIcon className="w-5 h-5" /><span>{buttonText}</span></>}
          </button>
        </div>
      </div>
      
{summaryData && activeTab === 'summary' && (
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 border border-white/20 animate-in slide-in-from-bottom duration-700">
            <div className="flex items-center mb-6">
              <Activity className="w-8 h-8 text-blue-600 mr-3" />
              <h2 className="text-2xl font-bold text-gray-800">AI Generated Summary</h2>
            </div>
            <div className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl p-6 border-l-4 border-blue-500">
              <iframe
                srcDoc={`
                  <!DOCTYPE html>
                  <html>
                    <head>
                      <style>
                        body {
                          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                          margin: 0;
                          padding: 20px;
                          color: #374151;
                          line-height: 1.6;
                          font-size: 16px;
                        }
                        h2 {
                          font-size: 1.5rem;
                          font-weight: 700;
                          color: #1f2937;
                          margin-bottom: 1rem;
                          margin-top: 0;
                        }
                        ul {
                          list-style-type: disc;
                          padding-left: 1.5rem;
                          margin: 0.5rem 0;
                        }
                        li {
                          margin-bottom: 0.5rem;
                          line-height: 1.6;
                        }
                        p {
                          margin: 0.5rem 0;
                        }
                      </style>
                    </head>
                    <body>
                      ${summaryData.summary}
                    </body>
                  </html>
                `}
                className="w-full border-0 rounded-lg"
                style={{ minHeight: '400px', height: 'auto' }}
                title="Summary Content"
              />
            </div>
            <div className="flex justify-end space-x-4 mt-6">
              <button onClick={() => updateSummary("replace")} disabled={!areButtonsEnabled} className="px-6 py-3 rounded-lg font-medium transition bg-red-600 text-white hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed">Replace</button>
              <button onClick={() => updateSummary("merge")} disabled={!areButtonsEnabled || isMerging} className="px-6 py-3 rounded-lg font-medium transition flex items-center justify-center space-x-2 bg-green-600 text-white hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed">{isMerging ? <LoadingSpinner text="Merging..." /> : 'Merge'}</button>
              <button onClick={() => updateSummary("add")} disabled={!areButtonsEnabled || !canAdd} className="px-6 py-3 rounded-lg font-medium transition bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed">Add This Version</button>
            </div>
        </div>
      )}
      
      {predictionData && activeTab === 'prediction' && (
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 border border-white/20 animate-in slide-in-from-bottom duration-700">
            <div className="flex items-center mb-6">
              <BarChart2 className="w-8 h-8 text-purple-600 mr-3" />
              <h2 className="text-2xl font-bold text-gray-800">AI Generated Prediction</h2>
            </div>
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-6 border-l-4 border-purple-500">
              <p className="text-gray-700 leading-relaxed text-lg">{predictionData.prediction}</p>
              {predictionData.confidence && (
                <div className="mt-4 text-right font-semibold text-purple-800">
                    Confidence: {(predictionData.confidence * 100).toFixed(0)}%
                </div>
              )}
            </div>
        </div>
      )}

      <div className="fixed bottom-6 left-6">
        <button onClick={onBackToSearch} disabled={isGenerating} className="px-4 py-2 rounded-lg shadow bg-gray-600 text-white hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed">Back to Search</button>
      </div>

      <AnimatePresence>
        {showHistory && (
          <motion.div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.div className="bg-white rounded-2xl shadow-xl p-6 w-11/12 max-w-3xl relative" initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}>
              <button onClick={() => setShowHistory(false)} className="absolute top-4 right-4 text-gray-400 hover:text-gray-700 transition"><X size={24}/></button>
              <h3 className="text-2xl font-bold mb-4 text-gray-800">Summary History</h3>
              <div className="max-h-[60vh] overflow-y-auto space-y-3 pr-2">
               {summaryHistory.length > 0 ? summaryHistory.map((item, idx) => (
                  <div key={idx} className="bg-white rounded-xl p-4 shadow-sm border flex justify-between items-center">
                    <div>
                      <p className="font-semibold text-gray-600">Version {summaryHistory.length - idx}</p>
                      <p className="text-gray-700 text-sm line-clamp-2 mt-1">{item.summary}</p>
                    </div>
                    <button onClick={() => setSelectedSummary(item)} className="ml-4 flex-shrink-0 bg-blue-100 text-blue-800 px-4 py-2 rounded-lg hover:bg-blue-200 text-sm font-semibold">View Full</button>
                  </div>
                )) : <div className="text-center py-8 text-gray-500"><p>No history found for this patient.</p></div>}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {selectedSummary && (
          <motion.div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.div className="bg-white rounded-2xl shadow-xl p-8 w-11/12 max-w-2xl relative max-h-[80vh] overflow-y-auto" initial={{ y: 50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 50, opacity: 0 }}>
              <button onClick={() => setSelectedSummary(null)} className="absolute top-4 right-4 text-gray-400 hover:text-gray-700 transition"><X size={24}/></button>
              <h3 className="text-2xl font-bold mb-4 text-gray-800">Full Summary</h3>
              <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">{selectedSummary.summary}</div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}


// ============================================================================
// --- 3. NAVIGATION COMPONENT ---
// ============================================================================

const ModeSwitch = ({ activeTab, onTabChange, disabled }: {
  activeTab: 'summary' | 'prediction',
  onTabChange: (tab: 'summary' | 'prediction') => void,
  disabled: boolean
}) => {
  const activeClasses = "bg-white text-blue-600 shadow-md";
  const inactiveClasses = "bg-transparent text-white/80 hover:bg-white/20";

  return (
    <div className="flex justify-center mb-8">
      <div className={`bg-blue-600/50 backdrop-blur-sm p-1 rounded-xl flex items-center space-x-1 transition ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
        <button
          onClick={() => onTabChange('summary')}
          disabled={disabled}
          className={`px-6 py-2 rounded-lg font-semibold transition-all duration-300 flex items-center space-x-2 ${activeTab === 'summary' ? activeClasses : inactiveClasses}`}
        >
          <BookOpen size={16} />
          <span>Summary</span>
        </button>
        <button
          onClick={() => onTabChange('prediction')}
          disabled={disabled}
          className={`px-6 py-2 rounded-lg font-semibold transition-all duration-300 flex items-center space-x-2 ${activeTab === 'prediction' ? activeClasses : inactiveClasses}`}
        >
          <BarChart2 size={16} />
          <span>Prediction</span>
        </button>
      </div>
    </div>
  );
};


// ============================================================================
// --- 4. MAIN APP COMPONENT ---
// ============================================================================
function App() {
  const [view, setView] = useState<'search' | 'summary'>('search');
  const [activeTab, setActiveTab] = useState<'summary' | 'prediction'>('summary');
  const [patientDetails, setPatientDetails] = useState<PatientDetails[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<PatientDetails | null>(null);
  const [uploadedPdf, setUploadedPdf] = useState<File | null>(null);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false); // State for summary
  const [isGeneratingPrediction, setIsGeneratingPrediction] = useState(false); // State for prediction
  // const API_URL = import.meta.env.VITE_API_URL;
  const [API_URL, setAPI_URL] = useState("");

  useEffect(() => {
    async function loadApiUrl() {
      const res = await fetch("/bk.json");
      const text = await res.text();
      const parts = text.trim().split("=");

      if (parts.length === 2) {
        setAPI_URL(parts[1].trim());
      }
    }

    loadApiUrl();
  }, []);
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
    setActiveTab('summary');
    setView('summary');
  };
  
  const handlePdfUpload = (file: File) => {
    setUploadedPdf(file);
    setSelectedPatient(null);
    setActiveTab('summary');
    setView('summary');
  }

  const handleBackToSearch = () => {
    setView('search');
    setSelectedPatient(null);
    setUploadedPdf(null);
    setPatientDetails([]);
  };
  
  const isAnyGenerationRunning = isGeneratingSummary || isGeneratingPrediction;

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
        
        {view === 'summary' && (
          <>
            <ModeSwitch 
              activeTab={activeTab} 
              onTabChange={setActiveTab} 
              disabled={isAnyGenerationRunning} 
            />
            <ActionPage
              patient={selectedPatient}
              initialPdfFile={uploadedPdf}
              onBackToSearch={handleBackToSearch}
              activeTab={activeTab}
              isGeneratingSummary={isGeneratingSummary}
              setIsGeneratingSummary={setIsGeneratingSummary}
              isGeneratingPrediction={isGeneratingPrediction}
              setIsGeneratingPrediction={setIsGeneratingPrediction}
            />
          </>
        )}
        
        <div className="text-center mt-12 text-gray-500">
          <p>© 2025 MediSummary AI{API_URL}</p>
        </div>
      </div>
    </div>
  );
}

export default App;
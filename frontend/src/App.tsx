import React, { useState, useEffect } from 'react';
import { User, Brain, AlertTriangle, FileText, Activity, History, Upload } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface SummaryData {
  summary: string;
  idea?: string | null;
}

function App() {
  const [patientId, setPatientId] = useState('');
  const [idea, setThoughts] = useState('');
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null);
  const [summaryHistory, setSummaryHistory] = useState<SummaryData[]>([]);
  const [errors, setErrors] = useState<{ patientId?: string; pdfFile?: string }>({});
  const [showHistory, setShowHistory] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState<SummaryData | null>(null);
  const API_URL = import.meta.env.VITE_API_URL;
  console.log("API URL:", API_URL);
  const [isMerging, setIsMerging] = useState(false);
  const [historyPatientId, setHistoryPatientId] = useState('');

  // States to control button disabled/enabled status
  const [areButtonsEnabled, setAreButtonsEnabled] = useState(false);
  const [isReEnableDisabled, setIsReEnableDisabled] = useState(false);
  const [canAdd, setCanAdd] = useState(false);
// ... (inside the App component)
  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault(); // Prevents the browser from opening the file

    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === "application/pdf") {
      setPdfFile(droppedFile);
      setIsModalOpen(false); // Close the modal after a successful drop
    } else {
      // Optional: Add a visual cue or a message for invalid file types
      alert("Please drop a PDF file.");
    }
  };


  const loadHistory = async () => {
    if (!historyPatientId.trim()) return;
    try {
      const response = await fetch(`${API_URL}/load_history`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patientId: historyPatientId }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Failed to load history");

      // Assuming the backend returns an array of history items
      setSummaryHistory(result.history || []);
    } catch (err) {
      console.error("Load history error:", err);
    }
  };
  // Effect to manage button states based on inputs
  useEffect(() => {
    if (patientId.trim() !== '' && !pdfFile) {
      // Logic for when PID is used
      setAreButtonsEnabled(true);
      setIsReEnableDisabled(true); // Re-enable button should be disabled
    } else if (pdfFile) {
      // Logic for when PDF is used
      setAreButtonsEnabled(false);
      setIsReEnableDisabled(false); // Re-enable button should be enabled
    } else {
      // Default state when no input is selected
      setAreButtonsEnabled(false);
      setIsReEnableDisabled(true);
    }
  }, [patientId, pdfFile]);

  const validateForm = () => {
    const newErrors: { patientId?: string; pdfFile?: string } = {};
    if (!patientId.trim() && !pdfFile) {
      newErrors.patientId = 'Patient ID or PDF is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const updateSummary = async (method: "replace" | "merge" | "add") => {
    if (!validateForm() || !summaryData) return;

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

      setSummaryData(cleanSummary);
      setSummaryHistory((prev) => [cleanSummary, ...prev]);
      await loadHistory();
      if (method === "add") {
        setCanAdd(false); // 🔒 disable add after use
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
      if (pdfFile) {
        const formData = new FormData();
        formData.append("pdf", pdfFile);

        const response = await fetch(`${API_URL}/start_summarisation`, {
          method: "POST",
          body: formData,
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Failed to extract PDF");

        const cleanSummary: SummaryData = {
          summary: result.summary,
          idea: result.idea ?? null,
        };

        setSummaryData(cleanSummary);
        setSummaryHistory((prev) => [cleanSummary, ...prev]);
        setCanAdd(true);
      } else {
        const response = await fetch(`${API_URL}/start_summarisation`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ patientId, idea }),
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Failed to generate summary");

        const cleanSummary: SummaryData = {
          summary: result.summary,
          idea: result.idea ?? (idea && idea.trim() !== "" ? idea : null),
        };

        setSummaryData(cleanSummary);
        setSummaryHistory((prev) => [cleanSummary, ...prev]);
        setCanAdd(true); 
      }
    } catch (err) {
      console.error("Generate error:", err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setPdfFile(event.target.files[0]);
      setIsModalOpen(false);
    }
  };

  return (
    <div
      className="min-h-screen bg-cover bg-center relative"
      style={{ backgroundImage: `url('https://www.sparrc.com/wp-content/uploads/2023/08/abt-us.jpg')`, backgroundAttachment: 'fixed' }}
    >
      {/* Semi-transparent overlay to lighten the background image */}
      <div className="absolute inset-0 bg-white opacity-70"></div>

      <div className="container mx-auto px-4 py-8 max-w-4xl relative z-10">

        {/* History Button */}
        <div className="fixed top-6 right-6 z-20">
          <button
            onClick={() => setShowHistory(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-xl shadow hover:bg-blue-700 transition"
          >
            <History className="w-5 h-5" />
            <span>View History</span>
          </button>
        </div>

        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <img src="https://www.sparrc.com/wp-content/uploads/2023/08/logo.png" alt="MediSummary AI Logo" className="h-12 mr-3" />
            <h1 className="text-4xl font-bold text-gray-800">MediSummary AI</h1>
          </div>
        </div>

        {/* Input Card */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl p-8 mb-8 border border-white/20">
          <div className="space-y-6">

            {/* Patient ID Input */}
            <div>
              <label className="flex items-center text-lg font-semibold text-gray-700 mb-3">
                <User className="w-5 h-5 mr-2 text-blue-600" />
                Patient ID / Username
              </label>
              <input
                type="text"
                value={patientId}
                onChange={(e) => {
                  setPatientId(e.target.value);
                  if (errors.patientId) setErrors((prev) => ({ ...prev, patientId: undefined }));
                }}
                disabled={!!pdfFile}
                className={`w-full px-4 py-3 rounded-xl border-2 transition-all duration-300 ${
                  pdfFile
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : errors.patientId
                      ? 'border-red-300 bg-red-50'
                      : 'border-gray-200 bg-white hover:border-blue-300 focus:border-blue-500'
                }`}
                placeholder="Enter patient ID or username"
              />
              {errors.patientId && (
                <p className="text-red-500 text-sm mt-2 flex items-center">
                  <AlertTriangle className="w-4 h-4 mr-1" />
                  {errors.patientId}
                </p>
              )}
            </div>

            {/* Upload PDF Button */}
            <button
              onClick={() => setIsModalOpen(true)}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-3 rounded-xl shadow hover:bg-blue-700 transition"
            >
              <Upload size={18} />
              {pdfFile ? "Change PDF" : "Upload PDF"}
            </button>

            {pdfFile && (
              <p className="mt-2 text-green-600 font-medium">
                Selected: {pdfFile.name}
              </p>
            )}

            {/* Thoughts */}
            {!pdfFile && (
              <div>
                <label className="flex items-center text-lg font-semibold text-gray-700 mb-3">
                  <FileText className="w-5 h-5 mr-2 text-blue-600" />
                  Your Thoughts (Optional)
                </label>
                <textarea
                  value={idea}
                  onChange={(e) => setThoughts(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 bg-white hover:border-blue-300 focus:border-blue-500 focus:outline-none resize-none"
                  placeholder="Add your clinical notes or observations..."
                />
              </div>
            )}

            {/* Generate */}
            <button
              onClick={generateSummary}
              disabled={isGenerating || (!patientId.trim() && !pdfFile)}
              className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center space-x-2"
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <Brain className="w-5 h-5" />
                  <span>Generate AI Summary</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Output */}
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
                {isMerging ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    <span>Merging...</span>
                  </>
                ) : (
                  <span>Merge</span>
                )}
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

        {/* Upload Modal */}
        <AnimatePresence>
          {isModalOpen && (
            <motion.div
              className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div
                className="bg-white rounded-2xl shadow-xl p-6 w-96"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
              >
                <h2 className="text-xl font-semibold text-center mb-4">
                  Upload Medical PDF
                </h2>
                <div
                  className="w-full flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-xl p-8 text-gray-500 cursor-pointer hover:border-blue-500 hover:text-blue-500 transition"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleDrop}
                >
                  <input
                    type="file"
                    id="pdf-upload"
                    accept="application/pdf"
                    className="hidden"
                    onChange={handleFileSelect}
                  />
                  <Upload size={28} />
                  <span className="mt-2">Drop file here or click to browse</span>
                  <label htmlFor="pdf-upload" className="mt-2 text-blue-500 hover:underline">
                    or click to browse
                  </label>
                </div>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="mt-6 w-full bg-gray-200 text-gray-700 px-4 py-2 rounded-xl hover:bg-gray-300 transition"
                >
                  Cancel
                </button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* History Modal */}
        <AnimatePresence>
          {showHistory && (
            <motion.div
              className="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div
                className="bg-white rounded-2xl shadow-xl p-6 w-11/12 max-w-3xl relative"
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0.9 }}
              >
                <button
                  onClick={() => setShowHistory(false)}
                  className="absolute top-3 right-3 text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
                <h3 className="text-xl font-bold mb-4">Summary History</h3>
                <div className="flex space-x-2 mb-4">
                  <input
                    type="text"
                    placeholder="Enter patient ID to load history"
                    value={historyPatientId}
                    onChange={(e) => setHistoryPatientId(e.target.value)}
                    className="flex-1 px-4 py-2 rounded-xl border border-gray-300 focus:border-blue-500"
                  />
                  <button
                    onClick={loadHistory}
                    className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition"
                  >
                    Load
                  </button>
                </div>
                <div className="grid grid-flow-col auto-cols-[300px] gap-4 overflow-x-auto pb-4">
                  {summaryHistory.map((item, idx) => (
                    <div
                      key={idx}
                            className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl p-4 shadow border border-blue-200"
                    >
                      <p className="text-gray-700 text-sm line-clamp-3">{item.summary}</p>
                      <button
                        onClick={() => setSelectedSummary(item)}
                        className="mt-3 w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition"
                      >
                        View
                      </button>
                    </div>
                  ))}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Full Summary Modal */}
        <AnimatePresence>
          {selectedSummary && (
            <motion.div
              className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div
                className="bg-white rounded-2xl shadow-xl p-8 w-11/12 max-w-2xl relative"
                initial={{ y: 50 }}
                animate={{ y: 0 }}
                exit={{ y: 50 }}
              >
                <button
                  onClick={() => setSelectedSummary(null)}
                  className="absolute top-3 right-3 text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
                <h3 className="text-xl font-bold mb-4">Full Summary</h3>
                <p className="text-gray-700 whitespace-pre-line">{selectedSummary.summary}</p>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Re-enable Button */}
        <div className="fixed bottom-6 left-6">
            <button
              onClick={() => {
                setPdfFile(null);
                setPatientId('');
                setErrors({});
                setSummaryData(null); // Add this line to reset the summary
              }}
              disabled={isReEnableDisabled}
              className={`px-4 py-2 rounded-lg shadow transition ${isReEnableDisabled ? 'bg-gray-400 text-gray-200 cursor-not-allowed' : 'bg-gray-600 text-white hover:bg-gray-700'}`}
            >
              Re-enable Patient ID
            </button>
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-gray-500">
          <p>© 2025 MediSummary AI</p>
        </div>
      </div>
    </div>
  );
}

export default App;
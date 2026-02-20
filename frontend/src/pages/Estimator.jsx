import { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Label } from '../components/ui/Label';
import {
  Upload,
  Image as ImageIcon,
  Sprout,
  AlertTriangle,
  CheckCircle2,
  Activity,
  FileImage,
  X,
  Zap,
  Save,
  Trash2
} from 'lucide-react';
import { uploadImageEstimateRequest, saveDetectionRequest, updatePredictionNotesRequest } from '../api/estimator';
import { getOrchardsRequest, getOrchardTreesRequest } from '../api/farming';
import { useAuth } from '../context/AuthContext';
import confetti from 'canvas-confetti'; // **Your changes** - Import confetti for success celebration

export default function EstimatorPage() {
  const { isGuest } = useAuth();
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [orchards, setOrchards] = useState([]);
  const [trees, setTrees] = useState([]);
  const [selectedOrchard, setSelectedOrchard] = useState('');
  const [selectedTree, setSelectedTree] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [confidence, setConfidence] = useState(0.5);
  const [notes, setNotes] = useState('');
  const [isSavingNote, setIsSavingNote] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [imagePath, setImagePath] = useState(null);
  const [isExcellentHealth, setIsExcellentHealth] = useState(false); // **Your changes** - Track if health is excellent for visual effects

const [batchFiles, setBatchFiles] = useState([]); // Raw files selected for batch processing
const [batchResults, setBatchResults] = useState([]); // [{id, url, status, data}, ...]
const [isProcessingBatch, setIsProcessingBatch] = useState(false);
const [progress, setProgress] = useState(0);



  // **Your changes** - Confetti celebration function for excellent health results
  const celebrateExcellentHealth = () => {
    const duration = 3000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

    function randomInRange(min, max) {
      return Math.random() * (max - min) + min;
    }

    const interval = setInterval(() => {
      const timeLeft = animationEnd - Date.now();

      if (timeLeft <= 0) {
        return clearInterval(interval);
      }

      const particleCount = 50 * (timeLeft / duration);

      confetti({
        ...defaults,
        particleCount,
        origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
        colors: ['#39FF14', '#00FF00', '#7FFF00']
      });
      confetti({
        ...defaults,
        particleCount,
        origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
        colors: ['#39FF14', '#00FF00', '#7FFF00']
      });
    }, 250);
  };

  useEffect(() => {
    if (!isGuest) {
      loadOrchards();
    }
  }, [isGuest]);

  useEffect(() => {
    if (selectedOrchard) {
      loadTrees(selectedOrchard);
    } else {
      setTrees([]);
      setSelectedTree('');
    }
  }, [selectedOrchard]);

  const loadOrchards = async () => {
    try {
      const res = await getOrchardsRequest();
      setOrchards(res.data);
    } catch (err) {
      console.error('Error loading orchards:', err);
    }
  };

  const loadTrees = async (orchardId) => {
    try {
      const res = await getOrchardTreesRequest(orchardId);
      setTrees(res.data);
    } catch (err) {
      console.error('Error loading trees:', err);
    }
  };

  const validateAndSetFile = (file) => {
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setError('Please select a valid image file');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('The file must be 10MB or less');
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError(null);
    setResult(null);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    validateAndSetFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      validateAndSetFile(files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedFile) {
      setError('Please select an image');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', selectedFile);

      const orchardId = selectedOrchard ? parseInt(selectedOrchard) : null;
      const treeId = selectedTree ? parseInt(selectedTree) : null;

      // **Your changes** - Set preview=true to process without saving to database
      const response = await uploadImageEstimateRequest(
        formData,
        orchardId,
        treeId,
        confidence,
        true  // preview mode - process only, do not save to DB
      );

      // Backend returns image with detection data in headers
      const processedImageBlob = response.data;
      const processedImageUrl = URL.createObjectURL(processedImageBlob);
      setPreviewUrl(processedImageUrl);
      // Debug: Log response headers
      console.log('Response headers:', response.headers);

      // Read detection results from response headers
      const result = {
        total_count: parseInt(response.headers['x-total-count'] || '0'),
        healthy_count: parseInt(response.headers['x-healthy-count'] || '0'),
        damaged_count: parseInt(response.headers['x-damaged-count'] || '0'),
        health_index: parseFloat(response.headers['x-health-index'] || '0'),
        inference_time_ms: parseFloat(response.headers['x-inference-time-ms'] || '0'),
        prediction_id: response.headers['x-prediction-id'] !== 'None' ? response.headers['x-prediction-id'] : null,
        id: response.headers['x-record-id'] !== 'None' ? response.headers['x-record-id'] : null,
        filename: selectedFile.name,
        created_at: new Date().toISOString(),
        processed_image_url: processedImageUrl,
        preview_mode: response.headers['x-preview-mode'] === 'true'
      };

      // Store image path for saving later
      const backendimgPath = response.headers['x-image-path'];
      setImagePath(backendimgPath);  // **Your changes** - Uncommented to properly store image_path
      

      setResult(result);
      setNotes('');
      setIsSaved(false);

      // **Your changes** - Trigger celebration if health index is excellent
      if (result.health_index > 90) {
        setIsExcellentHealth(true);
        setTimeout(() => {
          celebrateExcellentHealth();
        }, 300);
      } else {
        setIsExcellentHealth(false);
      }

      console.log('Parsed result:', result);
      console.log('Image path:', backendimgPath);

      // Update preview to show the processed image with bounding boxes
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
      setPreviewUrl(processedImageUrl);
    } catch (err) {
      console.error('Error processing image:', err);
      setError(err.response?.data?.detail || 'Error processing image');
    } finally {
      setLoading(false);
    }
  };
  
  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    setSelectedOrchard('');
    setSelectedTree('');
    setNotes('');
    setIsSaved(false);
    setImagePath(null);
    setIsExcellentHealth(false); // **Your changes** - Reset celebration state
  };

  const handleSaveDetection = async () => {
    if (!result || isSaved) return;

    try {
      setLoading(true);
      setError(null);

      const detectionData = {
        image_path: imagePath,
        healthy_count: result.healthy_count,
        damaged_count: result.damaged_count,
        total_count: result.total_count,
        health_index: result.health_index,
        user_notes: notes || null,
        inference_time_ms: result.inference_time_ms,
        orchard_id: selectedOrchard ? parseInt(selectedOrchard) : null,
        tree_id: selectedTree ? parseInt(selectedTree) : null
      };
      console.log("imagePath before saving:", imagePath);

      const response = await saveDetectionRequest(detectionData);

      console.log('Detection saved:', response.data);

      // Update result with saved IDs
      setResult({
        ...result,
        id: response.data.record_id,
        prediction_id: response.data.prediction_id,
        preview_mode: false
      });

      setIsSaved(true);
      alert('Detection saved successfully!');

    } catch (err) {
      console.error('Error saving detection:', err);
      
      // Extract error details from backend response
      let errorMessage = 'Failed to save detection';
      if (err.response?.data?.errors) {
        // Formatted validation errors from our custom handler
        const errors = err.response.data.errors;
        errorMessage = errors.map(e => `${e.field}: ${e.message}`).join(', ');
      } else if (err.response?.data?.detail) {
        // Direct error message
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDiscard = () => {
    // **Your changes** - Clean up processed image URL to prevent memory leak
    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }
    
    // Reset to original uploaded image preview
    setResult(null);
    setPreviewUrl(selectedFile ? URL.createObjectURL(selectedFile) : null);
    setNotes('');
    setImagePath(null);
    setIsSaved(false);
    setIsExcellentHealth(false); // **Your changes** - Reset celebration effects
  };

  const handleSaveNote = async () => {
  if (!result?.prediction_id) return;
  setIsSavingNote(true);
  try {
    console.log("Saving notes:", notes);
    await updatePredictionNotesRequest(result.prediction_id, notes);
    console.log("Note saved successfully! 🍏");
    alert("Note saved successfully! 🍏");
  } catch (err) {
    console.error("Error saving note:", err);
    setError("Failed to save note.");
  } finally {
    setIsSavingNote(false);
  }
};

  return (
    <div className="space-y-5 sm:space-y-6 lg:space-y-7">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2 flex items-center gap-2 sm:gap-3">
            <Zap className="w-6 h-6 sm:w-8 sm:h-8 text-apple-green" />
            Yield Estimator
          </h1>
          <p className="text-zinc-500 text-sm font-mono">
            {isGuest
              ? "Guest mode: test apple detection without limits"
              : "Upload an image for automatic apple detection"}
          </p>
        </div>
        {isGuest && (
          <div className="px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/30 text-yellow-500 text-xs font-mono animate-pulse">
            GUEST MODE ACTIVE
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 sm:gap-6 lg:gap-8">
        {/* Upload Section */}
        <div className="space-y-4">
          <Card className="border-zinc-800 bg-cyber-dark">
            <h3 className="text-white font-bold mb-4 flex items-center gap-2">
              <Upload className="w-5 h-5 text-apple-green" />
              Upload Image
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* File Input */}
              <div>
                <Label htmlFor="file-upload">Select Image</Label>
                <div
                  className={`mt-2 flex justify-center px-3 sm:px-6 pt-4 sm:pt-5 pb-4 sm:pb-6 border-2 border-dashed rounded-lg transition-colors ${
                    isDragging
                      ? 'border-apple-green bg-apple-green/5'
                      : 'border-zinc-800 hover:border-zinc-700'
                  }`}
                  onDragOver={handleDragOver}
                  onDragEnter={handleDragEnter}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <div className="space-y-1 text-center">
                    {previewUrl ? (
                      <div className="relative">
                        <img
                          src={previewUrl}
                          alt="Preview"
                          className="mx-auto max-h-48 sm:max-h-56 w-auto rounded-lg"
                        />
                        <button
                          type="button"
                          onClick={handleReset}
                          className="absolute top-2 right-2 p-2 bg-black/70 rounded-full hover:bg-black"
                        >
                          <X className="w-4 h-4 text-white" />
                        </button>
                      </div>
                    ) : (
                      <>
                        <FileImage className="mx-auto h-12 w-12 text-zinc-600" />
                        <div className="flex text-sm text-zinc-400">
                          <label
                            htmlFor="file-upload"
                            className="relative cursor-pointer rounded-md font-medium text-apple-green hover:text-apple-green-dim"
                          >
                            <span>Upload file</span>
                            <input
                              id="file-upload"
                              name="file-upload"
                              type="file"
                              accept="image/*"
                              className="sr-only"
                              onChange={handleFileChange}
                              required
                            />
                          </label>
                          <p className="pl-1">or drag and drop</p>
                        </div>
                        <p className="text-xs text-zinc-600">PNG, JPG up to 10MB</p>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Orchard Selection */}
              <div>
                <Label htmlFor="orchard">Orchard (Optional)</Label>
                <select
                  id="orchard"
                  value={selectedOrchard}
                  onChange={(e) => setSelectedOrchard(e.target.value)}
                  disabled={isGuest}
                  className={`w-full px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-white focus:outline-none focus:border-apple-green/50 ${isGuest ? 'opacity-50 cursor-not-allowed italic text-zinc-500' : ''
                    }`}
                >
                  <option value="">{isGuest ? "Not available in guest mode" : "Unassigned (Quick save)"}</option>
                  {!isGuest && orchards.map((orchard) => (
                    <option key={orchard.id} value={orchard.id}>
                      {orchard.name} - {orchard.location}
                    </option>
                  ))}
                </select>
                {isGuest && (
                  <p className="mt-1 text-[10px] text-zinc-600 font-mono">
                    * Sign in to link detections to your orchards
                  </p>
                )}
              </div>

              {/* Tree Selection */}
              {(!isGuest && selectedOrchard && trees.length > 0) && (
                <div>
                  <Label htmlFor="tree">Tree (Optional)</Label>
                  <select
                    id="tree"
                    value={selectedTree}
                    onChange={(e) => setSelectedTree(e.target.value)}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-white focus:outline-none focus:border-apple-green/50"
                  >
                    <option value="">Unassigned (General orchard)</option>
                    {trees.map((tree) => (
                      <option key={tree.id} value={tree.id}>
                        #{tree.tree_code} ({tree.tree_type || 'N/A'})
                      </option>
                    ))}
                  </select>
                </div>
              )}
              {/* Confidence Threshold Slider */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label className="text-xs text-zinc-500 uppercase font-mono">Confidence Threshold</Label>
                  <span className="text-apple-green font-mono font-bold">{(confidence * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="0.95"
                  step="0.05"
                  value={confidence}
                  onChange={(e) => setConfidence(parseFloat(e.target.value))}
                  className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-apple-green"
                />
                <p className="text-[10px] text-zinc-600 font-mono italic text-right">Higher values reduce false positives</p>
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-3 bg-apple-red/10 border border-apple-red/20 rounded-lg text-apple-red flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm">{error}</span>
                </div>
              )}

              {/* Submit Button */}
              <div className="flex gap-2">
                <Button
                  type="submit"
                  variant="primary"
                  className="flex-1"
                  isLoading={loading}
                  disabled={!selectedFile || loading}
                >
                  <Zap className="w-4 h-4" />
                  {loading ? 'Analyzing...' : 'Process Image'}
                </Button>
                {(selectedFile || result) && (
                  <Button type="button" variant="ghost" onClick={handleReset}>
                    Clear
                  </Button>
                )}
              </div>
            </form>
          </Card>
        </div>

        {/* Results Section */}
        <div className="space-y-4">
          {result ? (
            <>
              <Card className={`border-apple-green/30 bg-gradient-to-br from-zinc-900 to-black ${
                isExcellentHealth ? 'animate-pulse-slow border-apple-green shadow-[0_0_30px_rgba(57,255,20,0.5)]' : ''
              }`}> {/* **Your changes** - Add pulsing neon border for excellent health */}
                <div className="text-center">
                  <p className="text-xs text-zinc-500 font-mono uppercase mb-2">
                    Analysis Result
                  </p>
                  <div className="flex items-center justify-center gap-3 mb-4">
                    <CheckCircle2 className="w-8 h-8 text-apple-green" />
                      <h2 className="text-3xl sm:text-4xl font-bold text-white">
                        {result.total_count || 0}
                      </h2>
                  </div>
                  <p className="text-zinc-400">Detected Apples</p>
                </div>
              </Card>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Card className="border-zinc-800 bg-black/40">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-[11px] text-zinc-500 font-mono uppercase tracking-widest mb-1">
                        Healthy
                      </p>
                      <h3 className="text-2xl font-bold text-apple-green">
                        {result.healthy_count || 0}
                      </h3>
                    </div>
                    <div className="p-2 rounded-lg bg-zinc-900/50 text-apple-green">
                      <Sprout className="w-5 h-5" />
                    </div>
                  </div>
                </Card>

                <Card className="border-zinc-800 bg-black/40">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-[11px] text-zinc-500 font-mono uppercase tracking-widest mb-1">
                        Damaged
                      </p>
                      <h3 className="text-2xl font-bold text-apple-red">
                        {result.damaged_count || 0}
                      </h3>
                    </div>
                    <div className="p-2 rounded-lg bg-zinc-900/50 text-apple-red">
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                  </div>
                </Card>
              </div>

              <Card className="border-zinc-800 bg-cyber-dark">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-white font-bold flex items-center gap-2">
                    <Activity className="w-5 h-5 text-apple-green" />
                    Health Index
                  </h3>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-bold ${(result.health_index || 0) >= 80
                      ? 'bg-apple-green/10 text-apple-green'
                      : (result.health_index || 0) >= 50
                        ? 'bg-yellow-500/10 text-yellow-500'
                        : 'bg-red-500/10 text-red-500'
                      }`}
                  >
                    {(result.health_index || 0).toFixed(1)}%
                  </span>
                </div>
                <div className="bg-zinc-900 rounded-full h-4 overflow-hidden">
                  <div
                    className={`h-full transition-all ${(result.health_index || 0) >= 80
                      ? 'bg-apple-green'
                      : (result.health_index || 0) >= 50
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                      }`}
                    style={{ width: `${result.health_index || 0}%` }}
                  />
                </div>
              </Card>

              <Card className="border-zinc-800 bg-cyber-dark">
                <h3 className="text-white font-bold mb-3 flex items-center gap-2">
                  <FileImage className="w-5 h-5 text-apple-green" />
                  Details
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-zinc-500">File:</span>
                    <span className="text-white font-mono text-xs sm:text-sm break-all text-right">{result.filename || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Prediction ID:</span>
                    <span className="text-white font-mono text-xs sm:text-sm">#{result.id || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Timestamp:</span>
                    <span className="text-white font-mono text-xs">
                      {result.created_at
                        ? new Date(result.created_at).toLocaleString()
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              </Card>
            </>
          ) : (
            <Card className="border-zinc-800 bg-cyber-dark p-12 text-center">
              <ImageIcon className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
              <p className="text-zinc-500 mb-2">No results</p>
              <p className="text-sm text-zinc-600">
                Upload and process an image to see results here
              </p>
            </Card>
          )}
          {!isGuest && result && (
            <>
              {/* Preview Mode Banner */}
              {!isSaved && (
                <Card className="border-yellow-500/30 bg-yellow-500/5 p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <AlertTriangle className="w-5 h-5 text-yellow-500" />
                    <div>
                      <h4 className="text-yellow-500 font-bold text-sm">Preview Mode</h4>
                      <p className="text-zinc-400 text-xs">
                        Review the detection and decide if you want to save it to your database.
                      </p>
                    </div>
                  </div>
                </Card>
              )}

              {/* Notes Section */}
              <Card className="border-zinc-800 bg-black/60 p-4 border-l-2 border-l-apple-green">
                <Label className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest mb-3 block">
                  Field Observations {!isSaved && '(Optional)'}
                </Label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add notes about tree condition, pest damage, or other observations..."
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-sm text-zinc-300 focus:outline-none focus:border-apple-green/50 transition-all font-mono"
                  rows="3"
                  disabled={isSaved}
                />

                {/* Action Buttons */}
                {!isSaved ? (
                  <div className="mt-4 grid grid-cols-2 gap-3">
                    <Button
                      onClick={handleSaveDetection}
                      disabled={loading}
                      className="bg-apple-green hover:bg-apple-green/90 text-black font-bold py-3 rounded-lg transition-all flex items-center justify-center gap-2"
                    >
                      <Save className="w-4 h-4" />
                      {loading ? 'Saving...' : 'Save Detection'}
                    </Button>
                    <Button
                      onClick={handleDiscard}
                      disabled={loading}
                      variant="outline"
                      className="border-apple-red/30 hover:bg-apple-red/10 text-apple-red font-bold py-3 rounded-lg transition-all flex items-center justify-center gap-2"
                    >
                      <Trash2 className="w-4 h-4" />
                      Discard
                    </Button>
                  </div>
                ) : (
                  <div className="mt-4 p-3 bg-apple-green/10 border border-apple-green/30 rounded-lg text-center">
                    <CheckCircle2 className="w-6 h-6 text-apple-green mx-auto mb-2" />
                    <p className="text-apple-green font-bold text-sm">
                      ✅ Detection Saved Successfully!
                    </p>
                    <p className="text-zinc-500 text-xs mt-1">
                      Record ID: #{result.id} | Prediction ID: #{result.prediction_id}
                    </p>
                  </div>
                )}
              </Card>
            </>
          )}
          
        </div>
      </div>
    </div>
  );
}

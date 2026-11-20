import React, { useState, useEffect, useRef } from 'react';
import { translations } from '../i18n';
import { Language, ScanResult, ModelStatus } from '../types';
import { 
  Camera, Upload, Play, RefreshCw, AlertCircle, 
  CheckCircle2, Clock, Activity, Scale, DollarSign, VideoOff
} from 'lucide-react';

interface LiveScanPageProps {
  lang: Language;
  modelStatus: ModelStatus | null;
  activeReplayIndex?: number;
  onManualReplay?: (index: number) => void;
}

export const LiveScanPage: React.FC<LiveScanPageProps> = ({
  lang,
  modelStatus,
  activeReplayIndex = 0,
  onManualReplay
}) => {
  const t = translations[lang];

  // State
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionStats, setSessionStats] = useState({
    platesScanned: 0,
    totalLeftoverGrams: 0,
    totalCostBdt: 0,
    cleanPlatesCount: 0,
  });

  const [replayFrames, setReplayFrames] = useState<Array<{ index: number; filename: string; title: string }>>([]);
  const [isWebcamActive, setIsWebcamActive] = useState(false);
  const [isRecordingPlate, setIsRecordingPlate] = useState(false);
  const [recordSuccessToast, setRecordSuccessToast] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const webcamIntervalRef = useRef<any>(null);
  const isInferringRef = useRef<boolean>(false);
  const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null);

  // Fetch replay frames list on mount
  useEffect(() => {
    fetch('/api/scan/replay/frames')
      .then(res => res.json())
      .then(data => {
        if (data.frames) setReplayFrames(data.frames);
      })
      .catch(() => {});
  }, []);

  // Handle external demo step triggers
  useEffect(() => {
    if (activeReplayIndex !== undefined && replayFrames.length > 0) {
      triggerReplayStep(activeReplayIndex);
    }
  }, [activeReplayIndex, replayFrames.length]);

  // Ensure video element receives stream whenever webcam becomes active
  useEffect(() => {
    if (isWebcamActive && videoRef.current && streamRef.current) {
      const video = videoRef.current;
      video.muted = true;
      video.playsInline = true;
      if (video.srcObject !== streamRef.current) {
        video.srcObject = streamRef.current;
      }
      video.play().catch(e => console.warn("Video play error in sync effect:", e));
    }
  }, [isWebcamActive]);

  // Clean up streams & timers on unmount
  useEffect(() => {
    return () => {
      if (webcamIntervalRef.current) {
        clearInterval(webcamIntervalRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const triggerReplayStep = async (index: number) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`/api/scan/replay/step?frame_index=${index}`, { method: 'POST' });
      if (!res.ok) throw new Error("Replay step failed");
      const data: ScanResult = await res.json();
      setScanResult(data);
      updateSessionStats(data);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const updateSessionStats = (data: ScanResult) => {
    setSessionStats(prev => ({
      platesScanned: prev.platesScanned + 1,
      totalLeftoverGrams: prev.totalLeftoverGrams + data.total_leftover_grams,
      totalCostBdt: prev.totalCostBdt + data.total_cost_bdt,
      cleanPlatesCount: prev.cleanPlatesCount + (data.plate_state === 'empty_plate' ? 1 : 0),
    }));
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setErrorMsg(null);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('station_id', 'station-dish-return-1');
    formData.append('meal_period', 'lunch');

    try {
      const res = await fetch('/api/scan/frame', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error("Frame upload failed");
      const data: ScanResult = await res.json();

      // Read local image preview for overlay display
      const reader = new FileReader();
      reader.onload = (event) => {
        data.image_base64 = event.target?.result as string;
        setScanResult(data);
        updateSessionStats(data);
      };
      reader.readAsDataURL(file);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const startWebcam = async () => {
    setErrorMsg(null);

    // Verify secure context (localhost or HTTPS)
    if (typeof window !== "undefined" && !window.isSecureContext) {
      setErrorMsg("Camera access is blocked because the page is not in a Secure Context. Please use http://localhost:8000 or HTTPS (not 0.0.0.0 or network IP).");
      return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setErrorMsg("Camera API is not supported in this browser. Please use a modern browser (Chrome, Safari, Firefox, Edge) over localhost.");
      return;
    }

    try {
      let stream: MediaStream | null = null;

      // Attempt 1: Standard constraints without rigid facingMode (ideal for laptops & MacBooks)
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 }
          },
          audio: false
        });
      } catch (err1) {
        console.warn("Attempt 1 with ideal constraints failed, falling back to minimal:", err1);
      }

      // Attempt 2: Minimal fallback if ideal constraints failed
      if (!stream) {
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false
        });
      }

      streamRef.current = stream;

      // Attach stream to video element
      if (videoRef.current) {
        const video = videoRef.current;
        video.muted = true;
        video.playsInline = true;
        video.srcObject = stream;
        video.onloadedmetadata = () => {
          video.play().catch(e => console.warn("play on metadata warning:", e));
        };
        try {
          await video.play();
        } catch (playErr) {
          console.warn("Direct play warning:", playErr);
        }
      }

      setIsWebcamActive(true);
    } catch (err: any) {
      console.error("Webcam initialization failed:", err);
      setIsWebcamActive(false);

      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setErrorMsg("Camera permission denied. Please click the camera/tune icon in your browser address bar and allow Camera access, or check macOS System Settings > Privacy & Security > Camera.");
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        setErrorMsg("No camera device was detected on your machine. Please plug in or enable a webcam.");
      } else if (err.name === "NotReadableError" || err.name === "TrackStartError") {
        setErrorMsg("Camera is already in use by another application (e.g. Zoom, FaceTime, Photo Booth). Please close it and retry.");
      } else if (err.name === "OverconstrainedError") {
        setErrorMsg("Camera constraints could not be satisfied by your video hardware.");
      } else {
        setErrorMsg(`Camera error: ${err.message || err.name || "Failed to initialize webcam."}`);
      }
    }
  };

  const stopWebcam = () => {
    if (webcamIntervalRef.current) {
      clearInterval(webcamIntervalRef.current);
      webcamIntervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsWebcamActive(false);
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      if (ctx) ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    }
  };

  const captureWebcamFrame = (): string | null => {
    const video = videoRef.current;
    if (!video || video.readyState < 2 || !video.videoWidth || !video.videoHeight) {
      return null;
    }

    if (!offscreenCanvasRef.current) {
      offscreenCanvasRef.current = document.createElement('canvas');
      offscreenCanvasRef.current.width = 640;
      offscreenCanvasRef.current.height = 640;
    }

    const canvas = offscreenCanvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    const vw = video.videoWidth;
    const vh = video.videoHeight;
    const size = Math.min(vw, vh);
    const startX = (vw - size) / 2;
    const startY = (vh - size) / 2;

    // Crop center square and scale to 640x640 to match the YOLO input and UI canvas 1:1
    ctx.drawImage(video, startX, startY, size, size, 0, 0, 640, 640);
    return canvas.toDataURL('image/jpeg', 0.8);
  };

  // Real-time live inference loop (~400ms interval / 2.5 FPS)
  useEffect(() => {
    if (!isWebcamActive) {
      if (webcamIntervalRef.current) {
        clearInterval(webcamIntervalRef.current);
        webcamIntervalRef.current = null;
      }
      return;
    }

    let isSubscribed = true;

    const interval = setInterval(async () => {
      if (!isSubscribed || isInferringRef.current) return;

      const base64Data = captureWebcamFrame();
      if (!base64Data) return;

      isInferringRef.current = true;
      try {
        const res = await fetch('/api/scan/frame_base64', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image_base64: base64Data,
            station_id: 'station-dish-return-1',
            meal_period: 'lunch',
            image_name: 'webcam_live.jpg',
            persist: false // Live preview frames update UI detections without flooding the database
          })
        });

        if (res.ok && isSubscribed) {
          const data: ScanResult = await res.json();
          setScanResult(data);
        }
      } catch (e) {
        console.warn("Live frame inference error:", e);
      } finally {
        isInferringRef.current = false;
      }
    }, 400);

    webcamIntervalRef.current = interval;

    return () => {
      isSubscribed = false;
      clearInterval(interval);
      webcamIntervalRef.current = null;
    };
  }, [isWebcamActive]);

  // Operator manual "Log Plate Scrape" action
  const handleRecordPlate = async () => {
    if (!isWebcamActive) return;
    const base64Data = captureWebcamFrame();
    if (!base64Data) return;

    setIsRecordingPlate(true);
    try {
      const res = await fetch('/api/scan/frame_base64', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_base64: base64Data,
          station_id: 'station-dish-return-1',
          meal_period: 'lunch',
          image_name: 'webcam_record_plate.jpg',
          persist: true // Save event to database & update waste bins
        })
      });

      if (!res.ok) throw new Error("Plate recording failed");
      const data: ScanResult = await res.json();
      setScanResult(data);
      updateSessionStats(data);
      setRecordSuccessToast(`Logged ${data.total_leftover_grams}g waste (${data.plate_state.replace('_', ' ')})`);
      setTimeout(() => setRecordSuccessToast(null), 3000);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to record plate");
    } finally {
      setIsRecordingPlate(false);
    }
  };

  // Render bounding boxes over canvas
  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!scanResult) return;

    scanResult.boxes.forEach((b) => {
      const [x1, y1, x2, y2] = b.box;
      const rx = x1 * canvas.width;
      const ry = y1 * canvas.height;
      const rw = (x2 - x1) * canvas.width;
      const rh = (y2 - y1) * canvas.height;

      // Color coding: terracotta for high leftover, deep forest green for small/normal
      const strokeColor = b.estimated_grams > 80 ? "#c25e3e" : "#1e3a2b";
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 2.5;
      ctx.strokeRect(rx, ry, rw, rh);

      // Label background
      ctx.fillStyle = strokeColor;
      const labelText = `${lang === 'bn' ? b.name_bn : b.name_en} (${b.estimated_grams}g • ${(b.confidence * 100).toFixed(0)}%)`;
      ctx.font = "bold 11px -apple-system, BlinkMacSystemFont, sans-serif";
      const textWidth = ctx.measureText(labelText).width;
      const labelY = Math.max(0, ry - 19);
      const labelX = Math.min(rx, Math.max(0, canvas.width - (textWidth + 12)));
      ctx.fillRect(labelX, labelY, textWidth + 8, 19);

      // Label text
      ctx.fillStyle = "#ffffff";
      ctx.fillText(labelText, labelX + 4, labelY + 14);
    });
  }, [scanResult, lang]);

  return (
    <div className="space-y-4">
      
      {/* Top Banner & Session Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white border border-border p-3 rounded">
          <div className="text-[11px] text-zinc-500 font-medium">{t.plates_scanned}</div>
          <div className="text-xl font-semibold font-mono mt-0.5 text-zinc-900">
            {sessionStats.platesScanned}
          </div>
          <div className="text-[10px] text-emerald-700 mt-1 flex items-center">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            <span>{sessionStats.cleanPlatesCount} clean plates returned</span>
          </div>
        </div>

        <div className="bg-white border border-border p-3 rounded">
          <div className="text-[11px] text-zinc-500 font-medium">{t.total_wasted_grams}</div>
          <div className="text-xl font-semibold font-mono mt-0.5 text-zinc-900">
            {(sessionStats.totalLeftoverGrams / 1000).toFixed(2)} kg
          </div>
          <div className="text-[10px] text-zinc-500 mt-1">
            {sessionStats.totalLeftoverGrams.toFixed(0)}g total plate residue
          </div>
        </div>

        <div className="bg-white border border-border p-3 rounded">
          <div className="text-[11px] text-zinc-500 font-medium">{t.waste_cost}</div>
          <div className="text-xl font-semibold font-mono mt-0.5 text-terracotta">
            {t.currency} {sessionStats.totalCostBdt.toFixed(1)}
          </div>
          <div className="text-[10px] text-zinc-500 mt-1">
            Unavoidable dish scrape loss
          </div>
        </div>

        <div className="bg-white border border-border p-3 rounded">
          <div className="text-[11px] text-zinc-500 font-medium">{t.latency} / {t.fps}</div>
          <div className="text-xl font-semibold font-mono mt-0.5 text-zinc-900">
            {scanResult ? `${scanResult.inference_time_ms} ms` : "34 ms"}
          </div>
          <div className="text-[10px] text-zinc-500 mt-1 flex items-center">
            <Activity className="w-3 h-3 mr-1 text-emerald-600" />
            <span>{isWebcamActive ? "2.5 FPS (Live Stream)" : "Ready (On-Demand)"}</span>
          </div>
        </div>
      </div>

      {/* Error Alert Banner */}
      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3.5 rounded text-xs flex items-start justify-between">
          <div className="flex items-start space-x-2.5">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-900">Camera Notice</p>
              <p className="mt-0.5 text-rose-700 leading-relaxed">{errorMsg}</p>
            </div>
          </div>
          <button
            onClick={() => setErrorMsg(null)}
            className="text-rose-600 hover:text-rose-900 font-bold px-2 py-0.5 text-sm"
          >
            &times;
          </button>
        </div>
      )}

      {/* Main Scan Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        
        {/* Left 2 Cols: Video / Canvas Feed */}
        <div className="lg:col-span-2 bg-white border border-border rounded p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <div className="flex items-center space-x-2">
              <Camera className="w-4 h-4 text-primary" />
              <h3 className="font-semibold text-sm text-zinc-900">{t.camera_feed}</h3>
              <span className="text-xs text-zinc-400 font-mono">Station #1 (Dish Return)</span>
            </div>

            {/* Plate State Chip */}
            {scanResult && (
              <div className={`px-2.5 py-0.5 rounded text-xs font-medium border flex items-center space-x-1.5 ${
                scanResult.plate_state === 'empty_plate' 
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-300' 
                  : scanResult.plate_state === 'partial_leftover' 
                    ? 'bg-amber-50 text-amber-800 border-amber-300' 
                    : 'bg-rose-50 text-rose-800 border-rose-300'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  scanResult.plate_state === 'empty_plate' ? 'bg-emerald-600' : scanResult.plate_state === 'partial_leftover' ? 'bg-amber-600' : 'bg-rose-600'
                }`} />
                <span>
                  {scanResult.plate_state === 'empty_plate' ? t.empty_plate : scanResult.plate_state === 'partial_leftover' ? t.partial_leftover : t.full_plate}
                </span>
              </div>
            )}
          </div>

          {/* Canvas & Image Area */}
          <div className="relative my-4 aspect-square max-h-[460px] mx-auto bg-zinc-900 rounded overflow-hidden flex items-center justify-center border border-zinc-200 w-full">
            {isWebcamActive && (
              <div className="absolute top-2.5 left-2.5 z-20 bg-black/60 backdrop-blur-sm text-white text-[11px] px-2 py-0.5 rounded flex items-center space-x-1.5 border border-white/20">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="font-mono">LIVE • 2.5 FPS</span>
              </div>
            )}

            {recordSuccessToast && (
              <div className="absolute top-2.5 right-2.5 z-20 bg-emerald-700 text-white text-xs px-2.5 py-1 rounded shadow-md flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{recordSuccessToast}</span>
              </div>
            )}

            {/* Video element is permanently in DOM so videoRef.current is never null */}
            <video 
              ref={videoRef} 
              autoPlay 
              playsInline 
              muted 
              className={`w-full h-full object-cover ${isWebcamActive ? 'block' : 'hidden'}`} 
            />

            {!isWebcamActive && (
              scanResult?.image_base64 ? (
                <img 
                  src={scanResult.image_base64} 
                  alt="Dish Plate" 
                  className="w-full h-full object-cover" 
                />
              ) : (
                <div className="text-center p-6 text-zinc-400">
                  <Camera className="w-10 h-10 mx-auto mb-2 text-zinc-600" />
                  <p className="text-xs">Click Start Webcam, replay a plate, or upload an image to begin real-time scanning.</p>
                </div>
              )
            )}

            {/* Bounding Box Overlay Canvas */}
            <canvas 
              ref={canvasRef} 
              width={640} 
              height={640} 
              className="absolute inset-0 w-full h-full pointer-events-none z-10" 
            />

            {isLoading && (
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center text-white text-xs font-medium z-30">
                <RefreshCw className="w-5 h-5 animate-spin mr-2" />
                Analyzing frame & estimating grams...
              </div>
            )}
          </div>

          {/* Stream Controls */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-border">
            <div className="flex items-center space-x-2">
              {!isWebcamActive ? (
                <button
                  onClick={startWebcam}
                  className="px-3 py-1.5 bg-primary text-white text-xs font-medium rounded hover:bg-primary-hover transition-colors flex items-center space-x-1.5 cursor-pointer shadow-sm"
                >
                  <Camera className="w-3.5 h-3.5" />
                  <span>{t.start_webcam}</span>
                </button>
              ) : (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={stopWebcam}
                    className="px-3 py-1.5 bg-zinc-700 text-white text-xs font-medium rounded hover:bg-zinc-800 transition-colors flex items-center space-x-1.5 cursor-pointer"
                  >
                    <VideoOff className="w-3.5 h-3.5" />
                    <span>{t.stop_webcam}</span>
                  </button>

                  <button
                    onClick={handleRecordPlate}
                    disabled={isRecordingPlate}
                    className="px-3 py-1.5 bg-emerald-700 text-white text-xs font-medium rounded hover:bg-emerald-800 transition-colors flex items-center space-x-1.5 cursor-pointer shadow-sm"
                    title="Log current plate leftovers to database and session tally"
                  >
                    {isRecordingPlate ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    )}
                    <span>Log Plate Scrape</span>
                  </button>
                </div>
              )}

              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileUpload} 
                accept="image/*" 
                className="hidden" 
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-3 py-1.5 bg-zinc-100 text-zinc-700 text-xs font-medium rounded hover:bg-zinc-200 border border-border transition-colors flex items-center space-x-1 cursor-pointer"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>{t.upload_image}</span>
              </button>
            </div>

            {/* Replay 5 Sample Dishes Selector */}
            <div className="flex items-center space-x-1">
              <span className="text-[11px] text-zinc-500 mr-1 hidden sm:inline">Replay:</span>
              {[0, 1, 2, 3, 4].map((idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    triggerReplayStep(idx);
                    if (onManualReplay) onManualReplay(idx);
                  }}
                  className={`w-7 h-7 rounded text-xs font-mono font-medium border cursor-pointer ${
                    activeReplayIndex === idx 
                      ? 'bg-primary text-white border-primary' 
                      : 'bg-zinc-50 text-zinc-700 border-border hover:bg-zinc-100'
                  }`}
                  title={`Replay Plate #${idx + 1}`}
                >
                  P{idx + 1}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: Current Detection Breakdown */}
        <div className="bg-white border border-border rounded p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="font-semibold text-sm text-zinc-900">{t.food_detected}</h3>
              <span className="text-xs font-mono text-zinc-500">
                {scanResult?.boxes.length || 0} items
              </span>
            </div>

            {scanResult ? (
              <div className="divide-y divide-border mt-2">
                {scanResult.boxes.length === 0 ? (
                  <div className="py-8 text-center text-zinc-500 text-xs">
                    <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-600 mb-2" />
                    <p className="font-medium text-zinc-800">Clean Dish</p>
                    <p className="text-zinc-500 mt-0.5">No leftover food residue detected. Zero grams wasted.</p>
                  </div>
                ) : (
                  scanResult.boxes.map((b, idx) => (
                    <div key={idx} className="py-2.5 flex items-center justify-between text-xs">
                      <div>
                        <div className="font-medium text-zinc-900">
                          {lang === 'bn' ? b.name_bn : b.name_en}
                        </div>
                        <div className="text-[11px] text-zinc-400 font-mono mt-0.5">
                          Conf: {(b.confidence * 100).toFixed(0)}% • Category: {b.waste_category}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold font-mono text-zinc-900">
                          {b.estimated_grams} g
                        </div>
                        <div className="text-[11px] text-terracotta font-mono">
                          {t.currency} {b.cost_value_bdt.toFixed(1)}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <div className="py-12 text-center text-zinc-400 text-xs">
                Awaiting first plate scan...
              </div>
            )}
          </div>

          {/* Plate Metrics Footer */}
          {scanResult && (
            <div className="mt-4 pt-3 border-t border-border bg-zinc-50 -mx-4 -mb-4 p-4 rounded-b">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-zinc-600">Plate Area Coverage:</span>
                <span className="font-mono font-medium text-zinc-900">
                  {((scanResult.coverage_ratio || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-zinc-600">Estimated Leftover Grams:</span>
                <span className="font-mono font-bold text-zinc-900">
                  {scanResult.total_leftover_grams} g
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-zinc-600">Leftover Financial Cost:</span>
                <span className="font-mono font-semibold text-terracotta">
                  {t.currency} {scanResult.total_cost_bdt.toFixed(2)}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { Play, Pause, SkipForward, X, MessageSquare, ChevronUp, ChevronDown } from 'lucide-react';

interface DemoControllerProps {
  isActive: boolean;
  onClose: () => void;
  onNavigateTab: (tabId: string) => void;
  onTriggerReplayStep?: (frameIndex: number) => void;
}

export const DemoController: React.FC<DemoControllerProps> = ({
  isActive,
  onClose,
  onNavigateTab,
  onTriggerReplayStep,
}) => {
  const [seconds, setSeconds] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [showNotes, setShowNotes] = useState(true);

  const TOTAL_DURATION = 180; // 3 minutes = 180 seconds

  // Timeline Segments
  // 0-20: Intro
  // 20-70: Live Scan
  // 70-110: Analytics
  // 110-145: Agents
  // 145-170: Waste Collection
  // 170-180: Simulation & Architecture

  const segments = [
    {
      start: 0,
      end: 20,
      tab: 'scan',
      title: 'Problem Brief & -30% Target',
      notes: "Bangladeshi institutional canteens waste 25-30% of prepared food daily due to static batch-cooking and zero markdown mechanisms. WasteWiseAI targets a measurable, verifiable >=30% reduction via real-time computer vision and autonomous inventory agents.",
    },
    {
      start: 20,
      end: 70,
      tab: 'scan',
      title: 'Live Vision Ingestion & Quantity Estimation',
      notes: "Watch the camera feed. As students return plates, WasteWiseAI detects food classes (rice, dal, chicken curry), identifies plate states (clean vs leftover), and maps pixel areas to physical grams using portion calibration. Empty plates register zero waste while leftovers immediately increment the session counter.",
    },
    {
      start: 70,
      end: 110,
      tab: 'analytics',
      title: 'Waste Analytics & Batch Shelf-Life',
      notes: "The analytics engine aggregates waste by dish and meal period. Notice the alert: Bhuna Khichuri shows the highest leftover volume today. The kitchen inventory table shows current batch shelf-life countdowns.",
    },
    {
      start: 110,
      end: 145,
      tab: 'agents',
      title: 'Predictive Agents & Dynamic Discounting',
      notes: "The DemandForecastAgent adjusted today's prep for Friday prayer and rain. Notice the DynamicDiscountAgent auto-applying a 35% discount to the expiring Khichuri batch—converting potential waste into recovered revenue. The Agent Log narrates every decision.",
    },
    {
      start: 145,
      end: 170,
      tab: 'collection',
      title: 'Smart Waste Routing & Donation Manifest',
      notes: "Waste is segregated into 4 categories: edible surplus for NGO donation, animal feed for farms, organic compost, and general waste. When the compost bin hit 80%, the WasteCollectionAgent scheduled an automatic pickup manifest.",
    },
    {
      start: 170,
      end: 180,
      tab: 'simulation',
      title: 'Simulation Proof: >50% Food Waste Diverted',
      notes: "Our rigorous 30-day multi-seed simulation proves a 53.9% waste reduction (+/-0.5%) over the baseline policy while maintaining a 97.3% service level. Over 1,750 kg of food and 278,000 BDT saved per month.",
    },
  ];

  const currentSegment = segments.find(s => seconds >= s.start && seconds < s.end) || segments[0];

  useEffect(() => {
    if (!isActive) {
      setSeconds(0);
      setIsPaused(false);
      return;
    }

    if (isPaused) return;

    const interval = setInterval(() => {
      setSeconds((prev) => {
        if (prev >= TOTAL_DURATION) {
          clearInterval(interval);
          return TOTAL_DURATION;
        }
        return prev + 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, isPaused]);

  // Sync tab navigation and frame steps to demo timer
  useEffect(() => {
    if (!isActive) return;

    // Navigate to appropriate tab when entering new segment
    if (seconds === 0 || seconds === 20 || seconds === 70 || seconds === 110 || seconds === 145 || seconds === 170) {
      onNavigateTab(currentSegment.tab);
    }

    // Auto trigger plate replay steps during Live Scan segment (seconds 22, 32, 42, 52, 62)
    if (onTriggerReplayStep && seconds >= 22 && seconds <= 65 && seconds % 10 === 2) {
      const stepIdx = Math.floor((seconds - 22) / 10);
      onTriggerReplayStep(stepIdx % 5);
    }
  }, [seconds, isActive, currentSegment.tab, onNavigateTab, onTriggerReplayStep]);

  if (!isActive) return null;

  const formatTime = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSkipNext = () => {
    const nextSeg = segments.find(s => s.start > seconds);
    if (nextSeg) {
      setSeconds(nextSeg.start);
    } else {
      setSeconds(TOTAL_DURATION);
    }
  };

  return (
    <div className="fixed bottom-3 right-4 z-50 w-96 max-w-[calc(100vw-2rem)] bg-white border border-border shadow-xl rounded-md text-xs font-sans overflow-hidden">
      {/* Header & Controls */}
      <div className="bg-zinc-900 text-white px-3 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-semibold tracking-tight">3-Min Live Demo Mode</span>
          <span className="font-mono text-zinc-400 text-[11px]">
            {formatTime(seconds)} / {formatTime(TOTAL_DURATION)}
          </span>
        </div>
        <div className="flex items-center space-x-1.5">
          <button 
            onClick={() => setIsPaused(!isPaused)} 
            className="p-1 hover:bg-zinc-800 rounded text-zinc-300 hover:text-white"
            title={isPaused ? "Resume" : "Pause"}
          >
            {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
          </button>
          <button 
            onClick={handleSkipNext} 
            className="p-1 hover:bg-zinc-800 rounded text-zinc-300 hover:text-white"
            title="Skip to next segment"
          >
            <SkipForward className="w-3.5 h-3.5" />
          </button>
          <button 
            onClick={() => setShowNotes(!showNotes)} 
            className="p-1 hover:bg-zinc-800 rounded text-zinc-300 hover:text-white"
            title="Toggle Presenter Notes"
          >
            {showNotes ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
          <button 
            onClick={onClose} 
            className="p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-white ml-1"
            title="Exit Demo Mode"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-zinc-200 h-1">
        <div 
          className="bg-emerald-600 h-1 transition-all duration-300 ease-linear"
          style={{ width: `${(seconds / TOTAL_DURATION) * 100}%` }}
        />
      </div>

      {/* Current Segment Card */}
      <div className="p-3 bg-zinc-50 border-b border-border">
        <div className="flex items-center justify-between text-zinc-500 mb-1">
          <span className="uppercase text-[10px] font-semibold tracking-wider text-primary">
            Active Segment
          </span>
          <span className="font-mono text-[10px]">
            {formatTime(currentSegment.start)}–{formatTime(currentSegment.end)}
          </span>
        </div>
        <h4 className="font-medium text-zinc-900 text-xs">{currentSegment.title}</h4>
      </div>

      {/* Presenter Notes Overlay */}
      {showNotes && (
        <div className="p-3 bg-white text-zinc-700 max-h-48 overflow-y-auto leading-relaxed border-t border-border">
          <div className="flex items-center space-x-1 text-zinc-400 mb-1 font-medium text-[10px] uppercase">
            <MessageSquare className="w-3 h-3" />
            <span>Presenter Script & Key Points</span>
          </div>
          <p className="text-[11px] text-zinc-600">{currentSegment.notes}</p>
        </div>
      )}
    </div>
  );
};


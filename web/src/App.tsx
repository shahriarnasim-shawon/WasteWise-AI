import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DemoController } from './components/DemoController';
import { LiveScanPage } from './pages/LiveScanPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { PlateInsightsPage } from './pages/PlateInsightsPage';
import { AgentsPage } from './pages/AgentsPage';
import { WasteCollectionPage } from './pages/WasteCollectionPage';
import { SimulationPage } from './pages/SimulationPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { SettingsPage } from './pages/SettingsPage';
import { Language, ModelStatus } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('scan');
  const [lang, setLang] = useState<Language>('en');
  const [isDemoActive, setIsDemoActive] = useState<boolean>(false);
  const [activeReplayIndex, setActiveReplayIndex] = useState<number>(0);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);

  // Check URL query parameters for ?demo=1 on initial load
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('demo') === '1') {
      setIsDemoActive(true);
    }
  }, []);

  // Fetch model status on mount
  useEffect(() => {
    fetch('/api/model/status')
      .then(res => res.json())
      .then(data => setModelStatus(data))
      .catch(console.error);
  }, []);

  // Live WebSocket Connection for background events
  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/ws/events`;
      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          // Heartbeat or event notification
          if (msg.type === 'new_scan') {
            // Live scan received
          }
        } catch (e) {
          // Ignore parse errors
        }
      };
    } catch (e) {
      console.log("WebSocket connection unavailable, using HTTP endpoints");
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  const renderActivePage = () => {
    switch (currentTab) {
      case 'scan':
        return (
          <LiveScanPage 
            lang={lang} 
            modelStatus={modelStatus} 
            activeReplayIndex={activeReplayIndex}
            onManualReplay={(idx) => setActiveReplayIndex(idx)}
          />
        );
      case 'analytics':
        return <AnalyticsPage lang={lang} />;
      case 'insights':
        return <PlateInsightsPage lang={lang} />;
      case 'agents':
        return <AgentsPage lang={lang} />;
      case 'collection':
        return <WasteCollectionPage lang={lang} />;
      case 'simulation':
        return <SimulationPage lang={lang} />;
      case 'architecture':
        return <ArchitecturePage lang={lang} />;
      case 'settings':
        return <SettingsPage lang={lang} modelStatus={modelStatus} />;
      default:
        return <LiveScanPage lang={lang} modelStatus={modelStatus} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#fbfbfa] text-[#18181b]">
      {/* Top Navigation */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        lang={lang}
        setLang={setLang}
        isDemoActive={isDemoActive}
        toggleDemo={() => setIsDemoActive(!isDemoActive)}
        modelStatus={modelStatus}
      />

      {/* Main Page Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-5">
        {renderActivePage()}
      </main>

      {/* 3-Minute Demo Automation Overlay */}
      <DemoController
        isActive={isDemoActive}
        onClose={() => setIsDemoActive(false)}
        onNavigateTab={(tab) => setCurrentTab(tab)}
        onTriggerReplayStep={(stepIdx) => setActiveReplayIndex(stepIdx)}
      />

      {/* Footer */}
      <footer className="border-t border-border bg-white py-3 text-center text-xs text-zinc-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-1">
          <span>WasteWiseAI © 2026 • AI Builder Congress Hackathon</span>
          <span className="font-mono text-[11px] text-zinc-400">
            Render Ready • ONNX CPU &lt;400ms • Industry Food Waste Management
          </span>
        </div>
      </footer>
    </div>
  );
};


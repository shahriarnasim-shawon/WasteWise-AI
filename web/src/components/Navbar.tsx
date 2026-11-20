import React from 'react';
import { translations } from '../i18n';
import { Language, ModelStatus } from '../types';
import { 
  Camera, BarChart3, PieChart, Cpu, 
  Trash2, Sliders, Layers, Settings, Play, Globe
} from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  lang: Language;
  setLang: (l: Language) => void;
  isDemoActive: boolean;
  toggleDemo: () => void;
  modelStatus: ModelStatus | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  lang,
  setLang,
  isDemoActive,
  toggleDemo,
  modelStatus,
}) => {
  const t = translations[lang];

  const tabs = [
    { id: 'scan', label: t.nav_scan, icon: Camera },
    { id: 'analytics', label: t.nav_analytics, icon: BarChart3 },
    { id: 'insights', label: t.nav_insights, icon: PieChart },
    { id: 'agents', label: t.nav_agents, icon: Cpu },
    { id: 'collection', label: t.nav_collection, icon: Trash2 },
    { id: 'simulation', label: t.nav_simulation, icon: Sliders },
    { id: 'architecture', label: t.nav_architecture, icon: Layers },
    { id: 'settings', label: t.nav_settings, icon: Settings },
  ];

  return (
    <header className="border-b border-border bg-white sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          
          {/* Logo & Platform Info */}
          <div className="flex items-center space-x-3">
            <div className="w-7 h-7 bg-primary text-white rounded flex items-center justify-center font-bold text-sm tracking-wider">
              WW
            </div>
            <div>
              <span className="font-semibold text-sm tracking-tight text-zinc-900">
                {t.app_title}
              </span>
              <span className="hidden sm:inline-block text-xs text-zinc-600 ml-2 border-l border-zinc-300 pl-2">
                {t.app_subtitle}
              </span>
            </div>
          </div>

          {/* Model Status Pill & Demo Trigger */}
          <div className="flex items-center space-x-2">
            {modelStatus && (
              <div 
                className={`text-xs px-2 py-0.5 rounded border flex items-center space-x-1.5 ${
                  modelStatus.is_mock 
                    ? 'bg-amber-50 text-amber-900 border-amber-300' 
                    : 'bg-emerald-50 text-emerald-900 border-emerald-300'
                }`}
                title={modelStatus.mock_reason}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${modelStatus.is_mock ? 'bg-amber-600' : 'bg-emerald-600'}`} />
                <span className="font-mono">{modelStatus.is_mock ? t.mock_mode_badge : t.onnx_mode_badge}</span>
              </div>
            )}

            {/* Demo Mode Button */}
            <button
              onClick={toggleDemo}
              className={`text-xs px-3 py-1 rounded font-medium transition-colors flex items-center space-x-1 border ${
                isDemoActive 
                  ? 'bg-terracotta text-white border-terracotta' 
                  : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200 border-border'
              }`}
            >
              <Play className="w-3 h-3 fill-current" />
              <span>{isDemoActive ? 'Demo Active' : t.run_demo_button}</span>
            </button>

            {/* Language Toggle */}
            <button
              onClick={() => setLang(lang === 'en' ? 'bn' : 'en')}
              className="text-xs px-2 py-1 rounded border border-border bg-zinc-50 text-zinc-700 hover:bg-zinc-100 flex items-center space-x-1 font-mono"
            >
              <Globe className="w-3 h-3 text-zinc-700" />
              <span>{lang === 'en' ? 'BN' : 'EN'}</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 overflow-x-auto pb-1 scrollbar-none">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setCurrentTab(tab.id)}
                className={`flex items-center space-x-1.5 py-2 px-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
                  isActive 
                    ? 'border-primary text-primary font-semibold bg-primary/5' 
                    : 'border-transparent text-zinc-600 hover:text-zinc-900 hover:border-zinc-300'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-primary' : 'text-zinc-600'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};


import { useState, useEffect, useCallback } from 'react'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import StatusPanel from '@/components/StatusPanel'
import ActionsPanel from '@/components/ActionsPanel'
import ConsumablesPanel from '@/components/ConsumablesPanel'
import CleanRoomsPanel from '@/components/CleanRoomsPanel'
import RoutinesPanel from '@/components/RoutinesPanel'
import TriggersPanel from '@/components/TriggersPanel'
import WindowPlannerPanel from '@/components/WindowPlannerPanel'
import CleanSettingsPanel from '@/components/CleanSettingsPanel'
import SchedulePanel from '@/components/SchedulePanel'
import HistoryPanel from '@/components/HistoryPanel'
import ConnectivityBanner from '@/components/ConnectivityBanner'

type MobileTab = 'now' | 'clean' | 'plan' | 'info'
type RightTab = 'rooms' | 'routines' | 'triggers' | 'info'

function getStoredTab<T extends string>(key: string, fallback: T): T {
  return (sessionStorage.getItem(key) as T) || fallback
}

// Panel visibility on desktop: right-tab controls which panel shows
// Panel visibility on mobile: activeTab controls which panels show
function panelClass(mobileVisible: boolean, rightTab: RightTab, activeRightTab: RightTab): string {
  const mobileClass = mobileVisible ? '' : 'hidden md:block'
  const desktopClass = activeRightTab === rightTab ? '' : 'md:hidden'
  return [mobileClass, desktopClass].filter(Boolean).join(' ')
}

export default function App() {
  const [activeTab, setActiveTab] = useState<MobileTab>(() => getStoredTab('activeTab', 'now'))
  const [activeRightTab, setActiveRightTab] = useState<RightTab>(() => getStoredTab('activeRightTab', 'rooms'))
  const [refreshKey, setRefreshKey] = useState(0)

  const handleTabChange = (tab: MobileTab) => {
    setActiveTab(tab)
    sessionStorage.setItem('activeTab', tab)
  }

  const handleRightTabChange = (tab: RightTab) => {
    setActiveRightTab(tab)
    sessionStorage.setItem('activeRightTab', tab)
  }

  const refresh = useCallback(() => setRefreshKey(k => k + 1), [])

  useEffect(() => {
    const id = setInterval(refresh, 30000)
    return () => clearInterval(id)
  }, [refresh])

  return (
    <div
      className="min-h-svh"
      style={{
        padding: 'max(20px, env(safe-area-inset-top)) max(20px, env(safe-area-inset-right)) max(20px, env(safe-area-inset-bottom)) max(20px, env(safe-area-inset-left))',
        paddingBottom: 'calc(max(20px, env(safe-area-inset-bottom)) + 56px)',
      }}
    >
      {/* Header */}
      <header className="flex items-center gap-3 mb-6">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true">
          <circle cx="14" cy="14" r="13" stroke="#4f8ef7" strokeWidth="2"/>
          <circle cx="14" cy="14" r="6" fill="#4f8ef7" opacity="0.3"/>
          <circle cx="14" cy="14" r="2" fill="#4f8ef7"/>
          <circle cx="14" cy="4"  r="1.5" fill="#4f8ef7"/>
          <circle cx="14" cy="24" r="1.5" fill="#4f8ef7"/>
          <circle cx="4"  cy="14" r="1.5" fill="#4f8ef7"/>
          <circle cx="24" cy="14" r="1.5" fill="#4f8ef7"/>
        </svg>
        <h1 className="text-lg font-semibold">Vacuum Dashboard</h1>
        <span className="ml-auto text-xs text-muted-foreground">
          Auto-refreshes every 30s{' '}
          <button
            onClick={refresh}
            className="text-primary hover:underline bg-transparent border-0 cursor-pointer p-0 text-xs"
          >
            Refresh now
          </button>
        </span>
      </header>

      <ConnectivityBanner refreshKey={refreshKey} />

      {/* Cockpit */}
      <div className="flex flex-col gap-4 md:flex-row md:items-start">

        {/* Sidebar */}
        <div className="contents md:flex md:flex-col md:gap-4 md:w-80 md:shrink-0 md:sticky md:top-5 md:max-h-[calc(100vh-40px)] md:overflow-y-auto">
          <div className={activeTab === 'now' ? '' : 'hidden md:block'}>
            <StatusPanel refreshKey={refreshKey} />
          </div>
          <div className={activeTab === 'now' ? '' : 'hidden md:block'}>
            <ActionsPanel onStatusChange={refresh} />
          </div>
          <div className={activeTab === 'info' ? '' : 'hidden md:block'}>
            <ConsumablesPanel refreshKey={refreshKey} />
          </div>
        </div>

        {/* Right pane */}
        <div className="contents md:flex md:flex-col md:gap-4 md:flex-1 md:min-w-0 md:max-w-2xl">

          {/* Desktop right-pane tab bar */}
          <Tabs
            value={activeRightTab}
            onValueChange={(v) => handleRightTabChange(v as RightTab)}
            className="hidden md:block"
          >
            <TabsList className="w-full justify-start bg-card border border-border h-auto p-1.5">
              <TabsTrigger value="rooms">Rooms</TabsTrigger>
              <TabsTrigger value="routines">Routines</TabsTrigger>
              <TabsTrigger value="triggers">Triggers</TabsTrigger>
              <TabsTrigger value="info">Info</TabsTrigger>
            </TabsList>
          </Tabs>

          {/* Rooms — mobile: Clean tab; desktop: Rooms right-tab */}
          <div className={panelClass(activeTab === 'clean', 'rooms', activeRightTab)}>
            <CleanRoomsPanel refreshKey={refreshKey} />
          </div>

          {/* Routines — mobile: Clean tab; desktop: Routines right-tab */}
          <div className={panelClass(activeTab === 'clean', 'routines', activeRightTab)}>
            <RoutinesPanel refreshKey={refreshKey} />
          </div>

          {/* Schedule — mobile: Now tab (first); desktop: Info right-tab */}
          <div className={`${panelClass(activeTab === 'now', 'info', activeRightTab)} order-first md:order-none`}>
            <SchedulePanel refreshKey={refreshKey} />
          </div>

          {/* Window Planner — mobile: Plan tab; desktop: Triggers right-tab */}
          <div className={panelClass(activeTab === 'plan', 'triggers', activeRightTab)}>
            <WindowPlannerPanel />
          </div>

          {/* Triggers — mobile: Plan tab; desktop: Triggers right-tab */}
          <div className={panelClass(activeTab === 'plan', 'triggers', activeRightTab)}>
            <TriggersPanel refreshKey={refreshKey} />
          </div>

          {/* Clean Settings — mobile: Info tab; desktop: Info right-tab */}
          <div className={panelClass(activeTab === 'info', 'info', activeRightTab)}>
            <CleanSettingsPanel refreshKey={refreshKey} />
          </div>

          {/* History — mobile: Info tab; desktop: Info right-tab */}
          <div className={panelClass(activeTab === 'info', 'info', activeRightTab)}>
            <HistoryPanel refreshKey={refreshKey} />
          </div>
        </div>
      </div>

      {/* Mobile bottom tab bar */}
      <nav
        className="md:hidden fixed bottom-0 left-0 right-0 flex bg-card border-t border-border z-50"
        style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        {([
          { id: 'now' as const,   icon: '🏠', label: 'Now'   },
          { id: 'clean' as const, icon: '🧹', label: 'Clean' },
          { id: 'plan' as const,  icon: '📅', label: 'Plan'  },
          { id: 'info' as const,  icon: '📊', label: 'Info'  },
        ]).map(t => (
          <button
            key={t.id}
            onClick={() => handleTabChange(t.id)}
            className={`flex flex-col items-center gap-0.5 flex-1 bg-transparent border-0 cursor-pointer text-[10px] py-2 transition-colors ${activeTab === t.id ? 'text-primary' : 'text-muted-foreground'}`}
          >
            <span className="text-xl leading-none">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  )
}

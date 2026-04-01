import { useState, useEffect, useCallback, type ComponentType } from 'react'
import { Sparkles, CalendarDays, BarChart2, Orbit, TimerReset, RadioTower } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import StatusBar from '@/components/StatusBar'
import ConsumablesPanel from '@/components/ConsumablesPanel'
import CleanRoomsPanel from '@/components/CleanRoomsPanel'
import RoutinesPanel from '@/components/RoutinesPanel'
import TriggersPanel from '@/components/TriggersPanel'
import WindowPlannerPanel from '@/components/WindowPlannerPanel'
import CleanSettingsPanel from '@/components/CleanSettingsPanel'
import SchedulePanel from '@/components/SchedulePanel'
import HistoryPanel from '@/components/HistoryPanel'
import ConnectivityBanner from '@/components/ConnectivityBanner'

type MobileTab = 'schedule' | 'clean' | 'history'
type RightTab = 'clean' | 'triggers' | 'history'

const VALID_MOBILE_TABS: MobileTab[] = ['schedule', 'clean', 'history']
const VALID_RIGHT_TABS: RightTab[] = ['clean', 'triggers', 'history']

function getStoredMobileTab(): MobileTab {
  const stored = sessionStorage.getItem('activeTab') as MobileTab | null
  return stored && VALID_MOBILE_TABS.includes(stored) ? stored : 'schedule'
}

function getStoredRightTab(): RightTab {
  const stored = sessionStorage.getItem('activeRightTab') as RightTab | null
  return stored && VALID_RIGHT_TABS.includes(stored) ? stored : 'clean'
}

export default function App() {
  const [activeTab, setActiveTab] = useState<MobileTab>(getStoredMobileTab)
  const [activeRightTab, setActiveRightTab] = useState<RightTab>(getStoredRightTab)
  const [refreshKey, setRefreshKey] = useState(0)
  const mobileTabs: { id: MobileTab; icon: ComponentType<{ size?: number; strokeWidth?: number }>; label: string }[] = [
    { id: 'schedule', icon: CalendarDays, label: 'Schedule' },
    { id: 'clean', icon: Sparkles, label: 'Clean' },
    { id: 'history', icon: BarChart2, label: 'History' },
  ]

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
        padding: 'max(20px, env(safe-area-inset-top)) max(20px, env(safe-area-inset-right)) max(28px, env(safe-area-inset-bottom)) max(20px, env(safe-area-inset-left))',
        paddingBottom: 'calc(max(28px, env(safe-area-inset-bottom)) + 72px)',
      }}
    >
      <div className="mx-auto max-w-[1480px]">
        <header className="mb-3 md:hidden">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-sky-300/20 bg-sky-400/10 text-sky-200 shadow-[0_10px_28px_rgba(59,130,246,0.14)]">
              <Orbit size={16} strokeWidth={1.8} />
            </div>
            <div className="min-w-0">
              <p className="text-[9px] font-semibold uppercase tracking-[0.24em] text-sky-200/70">Vacuum Control Center</p>
              <h1 className="text-base font-semibold tracking-tight text-white">Schedule, clean, and recover faster.</h1>
            </div>
          </div>
        </header>

        <header className="mb-3 hidden rounded-[1.45rem] border border-white/10 bg-[linear-gradient(135deg,rgba(17,39,66,0.95),rgba(10,20,34,0.82))] px-4 py-3.5 shadow-[0_24px_64px_rgba(3,8,20,0.32)] backdrop-blur-xl md:block">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="min-w-0 max-w-2xl">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-sky-300/20 bg-sky-400/10 text-sky-200 shadow-[0_10px_28px_rgba(59,130,246,0.14)]">
                  <Orbit size={18} strokeWidth={1.8} />
                </div>
                <div className="min-w-0">
                  <p className="text-[9px] font-semibold uppercase tracking-[0.24em] text-sky-200/70">Vacuum Control Center</p>
                  <h1 className="text-lg font-semibold tracking-tight text-white lg:text-xl">Schedule, clean, and recover faster.</h1>
                </div>
              </div>
            </div>

            <div className="grid min-w-0 grid-cols-3 gap-2 lg:w-[500px] lg:max-w-[500px]">
              <div className="min-w-0 rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
                <div className="mb-0.5 flex items-center gap-1.5 text-[9px] uppercase tracking-[0.18em] text-slate-400">
                  <TimerReset size={14} />
                  Refresh
                </div>
                <div className="text-sm text-slate-200">30 sec</div>
              </div>
              <div className="min-w-0 rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
                <div className="mb-0.5 flex items-center gap-1.5 text-[9px] uppercase tracking-[0.18em] text-slate-400">
                  <CalendarDays size={14} />
                  Focus
                </div>
                <div className="text-sm text-slate-200">Schedule</div>
              </div>
              <div className="min-w-0 rounded-2xl border border-primary/30 bg-primary/10 px-3 py-2">
                <div className="mb-0.5 flex items-center gap-1.5 text-[9px] uppercase tracking-[0.18em] text-sky-200/80">
                  <RadioTower size={14} />
                  Action
                </div>
                <button
                  onClick={refresh}
                  className="cursor-pointer border-0 bg-transparent p-0 text-left text-sm font-medium text-white transition hover:text-sky-200"
                >
                  Refresh now
                </button>
              </div>
            </div>
          </div>
        </header>

        <ConnectivityBanner refreshKey={refreshKey} />

        <StatusBar refreshKey={refreshKey} onStatusChange={refresh} />

        <div className="hidden items-start gap-6 md:flex">
          <div className="min-w-0 flex-1">
            <SchedulePanel refreshKey={refreshKey} />
          </div>

          <div className="sticky top-5 flex max-h-[calc(100vh-72px)] w-[360px] shrink-0 flex-col gap-4 overflow-y-auto xl:w-[370px]">
            <Tabs
              value={activeRightTab}
              onValueChange={(v) => handleRightTabChange(v as RightTab)}
            >
              <TabsList className="grid h-auto w-full grid-cols-3 overflow-hidden rounded-[1.1rem] border border-white/10 bg-slate-950/40 p-1 backdrop-blur">
                <TabsTrigger value="clean" className="min-w-0 rounded-[0.8rem] px-1.5 py-2 text-[10px] font-medium text-slate-300 data-[state=active]:bg-white data-[state=active]:text-slate-950">
                  Clean
                </TabsTrigger>
                <TabsTrigger value="triggers" className="min-w-0 rounded-[0.8rem] px-1.5 py-2 text-[10px] font-medium text-slate-300 data-[state=active]:bg-white data-[state=active]:text-slate-950">
                  Triggers
                </TabsTrigger>
                <TabsTrigger value="history" className="min-w-0 rounded-[0.8rem] px-1.5 py-2 text-[10px] font-medium text-slate-300 data-[state=active]:bg-white data-[state=active]:text-slate-950">
                  History
                </TabsTrigger>
              </TabsList>
            </Tabs>

            {activeRightTab === 'clean' && (
              <div className="flex flex-col gap-4">
                <CleanSettingsPanel refreshKey={refreshKey} />
                <CleanRoomsPanel refreshKey={refreshKey} />
                <RoutinesPanel refreshKey={refreshKey} />
              </div>
            )}

            {/* Triggers tab: Triggers + Window Planner */}
            {activeRightTab === 'triggers' && (
              <div className="flex flex-col gap-4">
                <TriggersPanel refreshKey={refreshKey} />
                <WindowPlannerPanel />
              </div>
            )}

            {/* History tab: History + Consumables + Settings */}
            {activeRightTab === 'history' && (
              <div className="flex flex-col gap-4">
                <HistoryPanel refreshKey={refreshKey} />
                <ConsumablesPanel refreshKey={refreshKey} />
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-4 md:hidden">
          {activeTab === 'schedule' && (
            <>
              <SchedulePanel refreshKey={refreshKey} />
              <CleanSettingsPanel refreshKey={refreshKey} />
            </>
          )}

          {activeTab === 'clean' && (
            <>
              <CleanRoomsPanel refreshKey={refreshKey} />
              <RoutinesPanel refreshKey={refreshKey} />
              <TriggersPanel refreshKey={refreshKey} />
              <WindowPlannerPanel />
            </>
          )}

          {activeTab === 'history' && (
            <>
              <HistoryPanel refreshKey={refreshKey} />
              <ConsumablesPanel refreshKey={refreshKey} />
            </>
          )}
        </div>
      </div>

      <nav
        className="fixed bottom-3 left-1/2 z-50 flex w-[min(92vw,460px)] -translate-x-1/2 rounded-[1.6rem] border border-white/10 bg-slate-950/85 p-1.5 shadow-[0_20px_60px_rgba(2,8,20,0.45)] backdrop-blur-xl md:hidden"
        style={{ paddingBottom: 'calc(6px + env(safe-area-inset-bottom))' }}
      >
        {mobileTabs.map(t => (
          <button
            key={t.id}
            onClick={() => handleTabChange(t.id)}
            className={`flex flex-1 flex-col items-center gap-1 rounded-[1rem] border border-transparent px-3 py-2 text-[10px] transition ${
              activeTab === t.id
                ? 'bg-primary text-primary-foreground shadow-[0_10px_30px_rgba(96,165,250,0.35)]'
                : 'text-muted-foreground'
            }`}
          >
            <t.icon size={20} strokeWidth={1.75} />
            <span className="font-medium">{t.label}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}

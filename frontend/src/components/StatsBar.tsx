import { useStats } from '../hooks/useAccount'
import { useRebuildProjection } from '../hooks/useCommands'

export default function StatsBar() {
  const { data } = useStats()
  const rebuild  = useRebuildProjection()

  const stat = (label: string, value?: number) => (
    <div key={label} className="flex flex-col items-center">
      <span className="text-lg font-bold tabular text-white">{value ?? '—'}</span>
      <span className="text-[10px] text-muted uppercase tracking-wider">{label}</span>
    </div>
  )

  return (
    <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-surface/50">
      {/* Live indicator */}
      <div className="flex items-center gap-2">
        <div className="relative w-2 h-2">
          <div className="live-dot w-2 h-2 rounded-full bg-emerald relative" />
        </div>
        <span className="text-xs text-muted">Live</span>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-8">
        {stat('Events',       data?.total_events)}
        {stat('Accounts',     data?.total_accounts)}
        {stat('Transactions', data?.total_transactions)}
        {stat('Snapshots',    data?.total_snapshots)}
      </div>

      {/* Rebuild */}
      <button
        onClick={() => rebuild.mutate()}
        disabled={rebuild.isPending}
        className="text-xs text-muted hover:text-primary transition-colors disabled:opacity-40"
        title="Rebuild all read model projections from the event store"
      >
        {rebuild.isPending ? 'Rebuilding…' : '↺ Rebuild'}
      </button>
    </div>
  )
}
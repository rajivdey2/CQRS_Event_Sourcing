import { useRef, useEffect } from 'react'
import { format } from 'date-fns'
import type { DomainEvent } from '../types'

interface Props { events: DomainEvent[] }

const EVENT_COLORS: Record<string, string> = {
  AccountOpened:  'text-primary',
  MoneyDeposited: 'text-emerald',
  MoneyWithdrawn: 'text-rose',
  AccountClosed:  'text-muted',
}

export default function EventLogViewer({ events }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const prevLen   = useRef(events.length)

  useEffect(() => {
    if (events.length !== prevLen.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
      prevLen.current = events.length
    }
  }, [events.length])

  if (events.length === 0) {
    return (
      <div className="text-center py-12 text-muted text-sm">
        No events recorded yet.
      </div>
    )
  }

  return (
    <div className="font-mono text-xs space-y-0 max-h-[480px] overflow-y-auto pr-1">
      {/* Header */}
      <div className="grid grid-cols-[40px_1fr_140px_120px] gap-3 px-3 py-2
                      text-muted border-b border-border sticky top-0 bg-surface z-10">
        <span>V</span>
        <span>EVENT</span>
        <span className="hidden md:block">CORRELATION</span>
        <span className="text-right">TIMESTAMP</span>
      </div>

      {events.map((ev, i) => {
        const isNew = i >= prevLen.current - 1 && events.length > 1
        const color = EVENT_COLORS[ev.event_type] ?? 'text-white'
        const payload = ev.payload as Record<string, string>

        return (
          <div
            key={ev.id}
            className={`grid grid-cols-[40px_1fr_140px_120px] gap-3 px-3 py-2.5
                        border-b border-border/40 hover:bg-white/[0.02] transition-colors
                        ${isNew ? 'event-row-enter' : ''}`}
          >
            {/* Version badge */}
            <span className="text-muted/60 tabular self-start pt-0.5">{ev.version}</span>

            {/* Event type + payload preview */}
            <div>
              <span className={`font-medium ${color}`}>{ev.event_type}</span>
              <div className="text-muted/60 mt-0.5 text-[11px] space-y-0.5">
                {payload.amount && (
                  <div>amount: <span className="text-white/70">${payload.amount}</span></div>
                )}
                {payload.owner_name && (
                  <div>owner: <span className="text-white/70">{payload.owner_name}</span></div>
                )}
                {payload.description && (
                  <div className="truncate max-w-[200px]">
                    desc: <span className="text-white/70">{payload.description}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Correlation ID — first 8 chars */}
            <span className="text-muted/40 hidden md:block self-start pt-0.5 truncate">
              {ev.correlation_id ? ev.correlation_id.slice(0, 8) + '…' : '—'}
            </span>

            {/* Timestamp */}
            <span className="text-muted/60 text-right self-start pt-0.5 tabular">
              {format(new Date(ev.occurred_at), 'HH:mm:ss.SSS')}
            </span>
          </div>
        )
      })}
      <div ref={bottomRef} />
    </div>
  )
}
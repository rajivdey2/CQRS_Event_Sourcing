import { format } from 'date-fns'
import type { Account } from '../types'

interface Props {
  account: Account
  selected?: boolean
  onClick?: () => void
  compact?: boolean
}

export default function AccountCard({ account, selected = false, onClick, compact = false }: Props) {
  const balance  = parseFloat(account.balance)
  const isClosed = account.status === 'closed'

  if (compact) {
    return (
      <button
        onClick={onClick}
        className={`w-full text-left px-4 py-3.5 transition-all duration-150 border-l-2 ${
          selected
            ? 'bg-primary/10 border-primary'
            : 'border-transparent hover:bg-white/[0.03] hover:border-border'
        }`}
      >
        <div className="flex items-center justify-between mb-0.5">
          <span className="text-sm font-medium text-white truncate pr-2">{account.owner_name}</span>
          <span className={`text-sm font-semibold tabular ${
            isClosed ? 'text-muted' : balance >= 0 ? 'text-white' : 'text-rose'
          }`}>
            ${Math.abs(balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-mono text-muted/50 truncate">
            {account.account_id.slice(0, 8)}…
          </span>
          <span className={`text-[10px] ${isClosed ? 'text-muted/50' : 'text-emerald/70'}`}>
            {isClosed ? 'closed' : `v${account.version}`}
          </span>
        </div>
      </button>
    )
  }

  // Full card variant — used on a potential grid/list view
  return (
    <div
      onClick={onClick}
      className={`card p-5 cursor-pointer transition-all duration-150 hover:border-primary/40 ${
        selected ? 'border-primary' : ''
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-sm font-semibold text-white">{account.owner_name}</p>
          <p className="text-xs font-mono text-muted/50 mt-0.5">{account.account_id.slice(0, 12)}…</p>
        </div>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
          isClosed ? 'bg-white/5 text-muted' : 'bg-emerald/10 text-emerald'
        }`}>
          {isClosed ? 'Closed' : 'Active'}
        </span>
      </div>

      <div className="mb-3">
        <p className="text-2xl font-bold tabular text-white">
          ${Math.abs(balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          <span className="text-sm text-muted font-normal ml-1">{account.currency}</span>
        </p>
      </div>

      <div className="flex items-center justify-between text-xs text-muted">
        <span>{account.version} events</span>
        <span>{format(new Date(account.last_updated), 'MMM d, HH:mm')}</span>
      </div>
    </div>
  )
}
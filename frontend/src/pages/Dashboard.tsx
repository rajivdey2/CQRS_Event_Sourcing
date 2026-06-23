import { useState } from 'react'
import { format } from 'date-fns'
import { useAccounts } from '../hooks/useAccount'
import AccountDetail from './AccountDetail'
import OpenAccountModal from '../components/OpenAccountModal'
import StatsBar from '../components/StatsBar'
import ErrorBoundary from '../components/ErrorBoundary'
import { AccountListSkeleton } from '../components/Skeletons'
import type { Account } from '../types'

function AccountRow({ account, selected, onClick }: {
  account: Account
  selected: boolean
  onClick: () => void
}) {
  const balance  = parseFloat(account.balance)
  const isClosed = account.status === 'closed'

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

export default function Dashboard() {
  const { data: accounts = [], isLoading } = useAccounts()
  const [selectedId, setSelectedId]        = useState<string | null>(null)
  const [showModal, setShowModal]          = useState(false)

  return (
    <div className="h-screen flex flex-col bg-base overflow-hidden">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-primary/20 flex items-center justify-center">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6366F1" strokeWidth="2.5">
              <rect x="2" y="5" width="20" height="14" rx="2"/>
              <line x1="2" y1="10" x2="22" y2="10"/>
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white leading-none">Ledger</h1>
            <p className="text-[10px] text-muted mt-0.5">CQRS + Event Sourcing</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted hidden sm:block">
            {format(new Date(), 'MMM d, yyyy')}
          </span>
          <button
            onClick={() => setShowModal(true)}
            className="btn-primary flex items-center gap-1.5"
          >
            <span className="text-base leading-none">+</span>
            New Account
          </button>
        </div>
      </header>

      {/* Stats bar */}
      <ErrorBoundary fallback={<div className="h-11 border-b border-border" />}>
        <StatsBar />
      </ErrorBoundary>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Account list sidebar */}
        <aside className="w-64 shrink-0 border-r border-border overflow-y-auto">
          <div className="px-4 py-3 border-b border-border">
            <p className="text-[10px] text-muted uppercase tracking-widest font-medium">
              Accounts · {accounts.length}
            </p>
          </div>

          {isLoading && <AccountListSkeleton />}

          {!isLoading && accounts.length === 0 && (
            <div className="p-6 text-center">
              <p className="text-sm text-muted mb-1">No accounts yet</p>
              <p className="text-xs text-muted/50">Click "New Account" to begin</p>
            </div>
          )}

          {accounts.map(account => (
            <AccountRow
              key={account.account_id}
              account={account}
              selected={account.account_id === selectedId}
              onClick={() => setSelectedId(account.account_id)}
            />
          ))}
        </aside>

        {/* Detail panel */}
        <main className="flex-1 overflow-hidden p-4">
          {selectedId ? (
            <ErrorBoundary>
              <AccountDetail accountId={selectedId} />
            </ErrorBoundary>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="1.5">
                  <rect x="2" y="5" width="20" height="14" rx="2"/>
                  <line x1="2" y1="10" x2="22" y2="10"/>
                  <line x1="6" y1="15" x2="10" y2="15"/>
                </svg>
              </div>
              <p className="text-sm text-white font-medium mb-1">Select an account</p>
              <p className="text-xs text-muted max-w-[200px]">
                Choose from the sidebar or open a new account to see its event stream
              </p>
            </div>
          )}
        </main>
      </div>

      {showModal && (
        <OpenAccountModal
          onClose={() => setShowModal(false)}
          onCreated={id => setSelectedId(id)}
        />
      )}
    </div>
  )
}
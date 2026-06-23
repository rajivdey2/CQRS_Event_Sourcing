import { useState } from 'react'
import { useBalance, useTransactions, useEventStream } from '../hooks/useAccount'
import BalanceHero from '../components/BalanceHero'
import CommandPanel from '../components/CommandPanel'
import TransactionTable from '../components/TransactionTable'
import EventLogViewer from '../components/EventLogViewer'
import ErrorBoundary from '../components/ErrorBoundary'
import { BalanceHeroSkeleton, TransactionSkeleton, EventLogSkeleton } from '../components/Skeletons'

interface Props { accountId: string }
type Tab = 'transactions' | 'events'

export default function AccountDetail({ accountId }: Props) {
  const [tab, setTab] = useState<Tab>('transactions')

  const { data: account,      isLoading: loadingBal  } = useBalance(accountId)
  const { data: transactions = [], isLoading: loadingTx } = useTransactions(accountId)
  const { data: events = [],       isLoading: loadingEv } = useEventStream(accountId)

  if (loadingBal) {
    return (
      <div className="flex gap-4 h-full">
        <div className="flex-1 min-w-0 space-y-4">
          <BalanceHeroSkeleton />
          <div className="card p-4"><TransactionSkeleton /></div>
        </div>
        <div className="w-64 shrink-0">
          <div className="card p-5 space-y-3">
            {[1,2,3,4].map(i => (
              <div key={i} className="h-9 bg-white/5 rounded-lg animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!account) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-muted text-sm">Account not found.</div>
      </div>
    )
  }

  return (
    <div className="flex gap-4 h-full">
      {/* Main panel */}
      <div className="flex-1 min-w-0 overflow-y-auto space-y-4 pr-1">
        <ErrorBoundary>
          <BalanceHero account={account} transactions={transactions} />
        </ErrorBoundary>

        {/* Tabs */}
        <div className="card">
          <div className="flex border-b border-border px-4">
            {(['transactions', 'events'] as Tab[]).map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
                  tab === t
                    ? 'border-primary text-white'
                    : 'border-transparent text-muted hover:text-white'
                }`}
              >
                {t === 'transactions' ? (
                  <span>
                    Transactions{' '}
                    <span className="ml-1.5 text-xs bg-white/10 px-1.5 py-0.5 rounded-full">
                      {transactions.length}
                    </span>
                  </span>
                ) : (
                  <span>
                    Event Stream{' '}
                    <span className="ml-1.5 text-xs bg-primary/20 text-primary px-1.5 py-0.5 rounded-full">
                      {events.length}
                    </span>
                  </span>
                )}
              </button>
            ))}
          </div>

          <div className="p-4">
            {tab === 'transactions' ? (
              loadingTx
                ? <TransactionSkeleton />
                : <ErrorBoundary><TransactionTable transactions={transactions} /></ErrorBoundary>
            ) : (
              loadingEv
                ? <EventLogSkeleton />
                : <ErrorBoundary><EventLogViewer events={events} /></ErrorBoundary>
            )}
          </div>
        </div>
      </div>

      {/* Right sidebar — commands */}
      <div className="w-64 shrink-0">
        <ErrorBoundary>
          <CommandPanel account={account} />
        </ErrorBoundary>
      </div>
    </div>
  )
}
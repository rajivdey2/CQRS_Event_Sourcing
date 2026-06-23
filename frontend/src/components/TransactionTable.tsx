import { format } from 'date-fns'
import type { Transaction } from '../types'

interface Props { transactions: Transaction[] }

function Badge({ type }: { type: Transaction['event_type'] }) {
  if (type === 'MoneyDeposited') return <span className="badge-deposited">↑ Deposit</span>
  if (type === 'MoneyWithdrawn') return <span className="badge-withdrawn">↓ Withdraw</span>
  return <span className="badge-opened">◆ Opened</span>
}

export default function TransactionTable({ transactions }: Props) {
  if (transactions.length === 0) {
    return (
      <div className="text-center py-12 text-muted text-sm">
        No transactions yet. Send a deposit to get started.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-xs text-muted uppercase tracking-wider">
            <th className="text-left pb-3 pr-4 font-medium">Type</th>
            <th className="text-right pb-3 pr-4 font-medium">Amount</th>
            <th className="text-left pb-3 pr-4 font-medium hidden md:table-cell">Description</th>
            <th className="text-right pb-3 font-medium">Time</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/50">
          {transactions.map(tx => {
            const isCredit = tx.event_type === 'MoneyDeposited' || tx.event_type === 'AccountOpened'
            const amt = parseFloat(tx.amount ?? '0')
            return (
              <tr key={tx.id} className="group hover:bg-white/[0.02] transition-colors">
                <td className="py-3 pr-4">
                  <Badge type={tx.event_type} />
                </td>
                <td className={`py-3 pr-4 text-right font-semibold tabular ${
                  isCredit ? 'text-emerald' : 'text-rose'
                }`}>
                  {isCredit ? '+' : '-'}${amt.toFixed(2)}
                </td>
                <td className="py-3 pr-4 text-muted hidden md:table-cell truncate max-w-[200px]">
                  {tx.description || <span className="opacity-30">—</span>}
                </td>
                <td className="py-3 text-right text-muted text-xs tabular whitespace-nowrap">
                  {format(new Date(tx.occurred_at), 'MMM d, HH:mm:ss')}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
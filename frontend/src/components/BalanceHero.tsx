import { useEffect, useRef, useState } from 'react'
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis } from 'recharts'
import { format } from 'date-fns'
import type { Account, Transaction } from '../types'

interface Props {
  account: Account
  transactions: Transaction[]
}

// Animate a number from prev → next value
function useCountUp(target: number, duration = 600) {
  const [display, setDisplay] = useState(target)
  const prev = useRef(target)
  useEffect(() => {
    const start = prev.current
    const diff  = target - start
    if (diff === 0) return
    const startTime = performance.now()
    const tick = (now: number) => {
      const t = Math.min((now - startTime) / duration, 1)
      const ease = 1 - Math.pow(1 - t, 3)
      setDisplay(start + diff * ease)
      if (t < 1) requestAnimationFrame(tick)
      else prev.current = target
    }
    requestAnimationFrame(tick)
  }, [target, duration])
  return display
}

function buildChartData(transactions: Transaction[]) {
  // Build running balance from oldest → newest
  const sorted = [...transactions].reverse()
  let running = 0
  return sorted.map(tx => {
    const amt = parseFloat(tx.amount ?? '0')
    if (tx.event_type === 'MoneyDeposited' || tx.event_type === 'AccountOpened') running += amt
    else if (tx.event_type === 'MoneyWithdrawn') running -= amt
    return { date: format(new Date(tx.occurred_at), 'MMM d'), balance: running }
  })
}

export default function BalanceHero({ account, transactions }: Props) {
  const balance  = parseFloat(account.balance)
  const animated = useCountUp(balance)
  const chartData = buildChartData(transactions)
  const isPositive = balance >= 0
  const closed = account.status === 'closed'

  return (
    <div className="card p-6 mb-4">
      {/* Top row */}
      <div className="flex items-start justify-between mb-1">
        <div>
          <p className="text-xs text-muted uppercase tracking-widest font-medium mb-1">
            Current Balance
          </p>
          <div className="flex items-baseline gap-2">
            <span className="text-5xl font-bold tabular tracking-tight text-white balance-animate"
                  key={account.balance}>
              {animated.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className="text-xl text-muted font-medium">{account.currency}</span>
          </div>
        </div>
        <div className="text-right">
          <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${
            closed
              ? 'bg-white/5 text-muted'
              : 'bg-emerald/10 text-emerald'
          }`}>
            {closed ? 'Closed' : '● Active'}
          </span>
          <p className="text-xs text-muted mt-2">v{account.version} events</p>
        </div>
      </div>

      <p className="text-muted text-sm mb-4">{account.owner_name}</p>

      {/* Mini chart — only if we have data */}
      {chartData.length > 1 && (
        <div className="h-24 -mx-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="balGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={isPositive ? '#10B981' : '#F43F5E'} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={isPositive ? '#10B981' : '#F43F5E'} stopOpacity={0}   />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" hide />
              <Tooltip
                contentStyle={{ background: '#141929', border: '1px solid #1E2940', borderRadius: 8, fontSize: 12 }}
                formatter={(v: number) => [`$${v.toFixed(2)}`, 'Balance']}
              />
              <Area
                type="monotone"
                dataKey="balance"
                stroke={isPositive ? '#10B981' : '#F43F5E'}
                strokeWidth={2}
                fill="url(#balGrad)"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Account ID — monospace, subtle */}
      <p className="text-xs font-mono text-muted/50 mt-3 truncate">{account.account_id}</p>
    </div>
  )
}
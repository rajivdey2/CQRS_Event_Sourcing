import { useState } from 'react'
import { useDeposit, useWithdraw, useCloseAccount } from '../hooks/useCommands'
import type { Account } from '../types'

interface Props {
  account: Account
}

type Mode = 'deposit' | 'withdraw'

export default function CommandPanel({ account }: Props) {
  const [mode, setMode]       = useState<Mode>('deposit')
  const [amount, setAmount]   = useState('')
  const [desc, setDesc]       = useState('')
  const [feedback, setFeedback] = useState<{ ok: boolean; msg: string } | null>(null)

  const deposit  = useDeposit(account.account_id)
  const withdraw = useWithdraw(account.account_id)
  const close    = useCloseAccount(account.account_id)

  const isBusy   = deposit.isPending || withdraw.isPending
  const isClosed = account.status === 'closed'

  const flash = (ok: boolean, msg: string) => {
    setFeedback({ ok, msg })
    setTimeout(() => setFeedback(null), 3000)
  }

  const handleSubmit = async () => {
    if (!amount || isNaN(parseFloat(amount))) return
    try {
      if (mode === 'deposit') await deposit.mutateAsync({ amount, desc })
      else                    await withdraw.mutateAsync({ amount, desc })
      setAmount('')
      setDesc('')
      flash(true, mode === 'deposit' ? `+$${amount} deposited` : `-$${amount} withdrawn`)
    } catch (e: unknown) {
      flash(false, e instanceof Error ? e.message : 'Something went wrong')
    }
  }

  return (
    <div className="card p-5">
      <h3 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">
        Send Command
      </h3>

      {isClosed && (
        <div className="text-xs text-muted bg-white/5 rounded-lg px-3 py-2 mb-4">
          Account is closed — no further operations allowed.
        </div>
      )}

      {/* Mode toggle */}
      {!isClosed && (
        <>
          <div className="flex gap-1 mb-4 bg-base rounded-lg p-1">
            {(['deposit', 'withdraw'] as Mode[]).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 text-sm font-medium py-1.5 rounded-md transition-all duration-150 ${
                  mode === m
                    ? m === 'deposit'
                      ? 'bg-emerald/20 text-emerald'
                      : 'bg-rose/20 text-rose'
                    : 'text-muted hover:text-white'
                }`}
              >
                {m.charAt(0).toUpperCase() + m.slice(1)}
              </button>
            ))}
          </div>

          <div className="space-y-3">
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted text-sm">$</span>
              <input
                type="number"
                min="0.01"
                step="0.01"
                placeholder="0.00"
                value={amount}
                onChange={e => setAmount(e.target.value)}
                className="input pl-7 tabular"
              />
            </div>
            <input
              type="text"
              placeholder="Description (optional)"
              value={desc}
              onChange={e => setDesc(e.target.value)}
              className="input"
              maxLength={255}
            />
            <button
              onClick={handleSubmit}
              disabled={isBusy || !amount}
              className={`w-full py-2.5 rounded-lg text-sm font-semibold transition-all duration-150
                active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100
                ${mode === 'deposit'
                  ? 'bg-emerald text-white hover:bg-emerald/90'
                  : 'bg-rose text-white hover:bg-rose/90'
                }`}
            >
              {isBusy ? 'Processing…' : mode === 'deposit' ? 'Deposit' : 'Withdraw'}
            </button>
          </div>
        </>
      )}

      {/* Feedback toast */}
      {feedback && (
        <div className={`mt-3 text-xs font-medium px-3 py-2 rounded-lg transition-all ${
          feedback.ok ? 'bg-emerald/10 text-emerald' : 'bg-rose/10 text-rose'
        }`}>
          {feedback.msg}
        </div>
      )}

      {/* Close account */}
      {!isClosed && (
        <div className="mt-6 pt-4 border-t border-border">
          <button
            onClick={() => { if (confirm('Close this account?')) close.mutate('User request') }}
            disabled={close.isPending}
            className="text-xs text-muted hover:text-rose transition-colors"
          >
            Close account
          </button>
        </div>
      )}
    </div>
  )
}
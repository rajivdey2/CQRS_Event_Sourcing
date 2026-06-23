import { useState } from 'react'
import { useOpenAccount } from '../hooks/useCommands'

interface Props { onClose: () => void; onCreated: (id: string) => void }

export default function OpenAccountModal({ onClose, onCreated }: Props) {
  const [name, setName]       = useState('')
  const [balance, setBalance] = useState('0.00')
  const [error, setError]     = useState('')
  const open = useOpenAccount()

  const handleSubmit = async () => {
    if (!name.trim()) { setError('Owner name is required'); return }
    try {
      const res = await open.mutateAsync({ owner_name: name, initial_balance: balance, currency: 'USD' })
      onCreated(res.account_id)
      onClose()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to open account')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
         onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="card w-full max-w-md p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-white">Open New Account</h2>
          <button onClick={onClose} className="text-muted hover:text-white text-xl leading-none">×</button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs text-muted mb-1.5">Owner Name</label>
            <input
              autoFocus
              type="text"
              placeholder="e.g. Alice Chen"
              value={name}
              onChange={e => setName(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1.5">Initial Balance (USD)</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted text-sm">$</span>
              <input
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                value={balance}
                onChange={e => setBalance(e.target.value)}
                className="input pl-7 tabular"
              />
            </div>
          </div>
        </div>

        {error && (
          <p className="mt-3 text-xs text-rose">{error}</p>
        )}

        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="btn-ghost flex-1">Cancel</button>
          <button onClick={handleSubmit} disabled={open.isPending} className="btn-primary flex-1">
            {open.isPending ? 'Opening…' : 'Open Account'}
          </button>
        </div>
      </div>
    </div>
  )
}
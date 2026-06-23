export interface Account {
  account_id: string
  owner_name: string
  balance: string
  currency: string
  status: 'active' | 'closed'
  version: number
  last_updated: string
}

export interface Transaction {
  id: string
  account_id: string
  event_type: 'AccountOpened' | 'MoneyDeposited' | 'MoneyWithdrawn'
  amount: string
  balance_after: string | null
  description: string | null
  occurred_at: string
}

export interface DomainEvent {
  id: string
  stream_id: string
  version: number
  event_type: string
  payload: Record<string, unknown>
  correlation_id: string | null
  occurred_at: string
}

export interface Stats {
  total_events: number
  total_streams: number
  total_accounts: number
  total_transactions: number
  total_snapshots: number
}
import client from './client'
import type { Account, Transaction, DomainEvent, Stats } from '../types'

// ── Queries ───────────────────────────────────────────────────────────────────
export const getAccounts = async (): Promise<Account[]> => {
  const r = await client.get<Account[]>('/queries/accounts')
  return Array.isArray(r.data) ? r.data : []
}

export const getBalance = async (id: string): Promise<Account> => {
  const r = await client.get<Account>(`/queries/accounts/${id}/balance`)
  return r.data
}

export const getTransactions = async (id: string): Promise<Transaction[]> => {
  const r = await client.get<Transaction[]>(`/queries/accounts/${id}/transactions`)
  return Array.isArray(r.data) ? r.data : []
}

export const getEventStream = async (id: string): Promise<DomainEvent[]> => {
  const r = await client.get<DomainEvent[]>(`/queries/accounts/${id}/events`)
  return Array.isArray(r.data) ? r.data : []
}

export const getStats = async (): Promise<Stats> => {
  const r = await client.get<Stats>('/admin/stats')
  return r.data
}

// ── Commands ──────────────────────────────────────────────────────────────────
export const openAccount = async (data: {
  owner_name: string
  initial_balance: string
  currency: string
}): Promise<{ account_id: string }> => {
  const r = await client.post<{ account_id: string }>('/commands/accounts', data)
  return r.data
}

export const deposit = (id: string, amount: string, description?: string) =>
  client.post(`/commands/accounts/${id}/deposit`, { amount, description: description ?? '' })

export const withdraw = (id: string, amount: string, description?: string) =>
  client.post(`/commands/accounts/${id}/withdraw`, { amount, description: description ?? '' })

export const closeAccount = (id: string, reason?: string) =>
  client.post(`/commands/accounts/${id}/close`, { reason: reason ?? '' })

export const rebuildProjection = async (): Promise<{ replayed: number; status: string }> => {
  const r = await client.post<{ replayed: number; status: string }>('/admin/rebuild-projection')
  return r.data
}
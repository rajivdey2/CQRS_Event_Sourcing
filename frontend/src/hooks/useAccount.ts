import { useQuery } from '@tanstack/react-query'
import { getAccounts, getBalance, getTransactions, getEventStream, getStats } from '../api/accounts'

export const useAccounts = () =>
  useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts,
    refetchInterval: 5000,
    select: (data) => (Array.isArray(data) ? data : []),
  })

export const useBalance = (id: string) =>
  useQuery({
    queryKey: ['balance', id],
    queryFn: () => getBalance(id),
    enabled: !!id,
    refetchInterval: 3000,
  })

export const useTransactions = (id: string) =>
  useQuery({
    queryKey: ['transactions', id],
    queryFn: () => getTransactions(id),
    enabled: !!id,
    select: (data) => (Array.isArray(data) ? data : []),
  })

export const useEventStream = (id: string) =>
  useQuery({
    queryKey: ['events', id],
    queryFn: () => getEventStream(id),
    enabled: !!id,
    select: (data) => (Array.isArray(data) ? data : []),
  })

export const useStats = () =>
  useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    refetchInterval: 5000,
  })
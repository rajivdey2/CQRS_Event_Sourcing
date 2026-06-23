import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deposit, withdraw, openAccount, closeAccount, rebuildProjection } from '../api/accounts'

const invalidateAll = (qc: ReturnType<typeof useQueryClient>, id?: string) => {
  qc.invalidateQueries({ queryKey: ['accounts'] })
  qc.invalidateQueries({ queryKey: ['stats'] })
  if (id) {
    qc.invalidateQueries({ queryKey: ['balance', id] })
    qc.invalidateQueries({ queryKey: ['transactions', id] })
    qc.invalidateQueries({ queryKey: ['events', id] })
  }
}

export const useDeposit = (id: string) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ amount, desc }: { amount: string; desc: string }) => deposit(id, amount, desc),
    onSuccess: () => invalidateAll(qc, id),
  })
}

export const useWithdraw = (id: string) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ amount, desc }: { amount: string; desc: string }) => withdraw(id, amount, desc),
    onSuccess: () => invalidateAll(qc, id),
  })
}

export const useOpenAccount = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: openAccount,
    onSuccess: () => invalidateAll(qc),
  })
}

export const useCloseAccount = (id: string) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (reason: string) => closeAccount(id, reason),
    onSuccess: () => invalidateAll(qc, id),
  })
}

export const useRebuildProjection = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: rebuildProjection,
    onSuccess: () => { qc.invalidateQueries() },
  })
}
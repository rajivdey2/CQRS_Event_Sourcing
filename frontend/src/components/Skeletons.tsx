function Pulse({ className }: { className: string }) {
  return <div className={`bg-white/5 rounded-lg animate-pulse ${className}`} />
}

export function BalanceHeroSkeleton() {
  return (
    <div className="card p-6 mb-4">
      <Pulse className="h-3 w-24 mb-3" />
      <Pulse className="h-10 w-48 mb-2" />
      <Pulse className="h-4 w-32 mb-4" />
      <Pulse className="h-24 w-full" />
    </div>
  )
}

export function TransactionSkeleton() {
  return (
    <div className="space-y-3 py-2">
      {[1, 2, 3, 4, 5].map(i => (
        <div key={i} className="flex items-center justify-between gap-4">
          <Pulse className="h-5 w-20" />
          <Pulse className="h-4 w-16" />
          <Pulse className="h-4 flex-1 hidden md:block" />
          <Pulse className="h-4 w-24" />
        </div>
      ))}
    </div>
  )
}

export function AccountListSkeleton() {
  return (
    <div className="p-3 space-y-2">
      {[1, 2, 3].map(i => (
        <Pulse key={i} className="h-14 w-full" />
      ))}
    </div>
  )
}

export function EventLogSkeleton() {
  return (
    <div className="space-y-2 py-2 font-mono">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="flex gap-4 items-start">
          <Pulse className="h-4 w-6" />
          <div className="flex-1 space-y-1">
            <Pulse className="h-4 w-32" />
            <Pulse className="h-3 w-48" />
          </div>
          <Pulse className="h-4 w-20 hidden md:block" />
          <Pulse className="h-4 w-20" />
        </div>
      ))}
    </div>
  )
}
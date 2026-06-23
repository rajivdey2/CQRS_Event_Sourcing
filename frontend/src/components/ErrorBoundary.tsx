import { Component, type ReactNode } from 'react'

interface Props  { children: ReactNode; fallback?: ReactNode }
interface State  { error: Error | null }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  render() {
    if (this.state.error) {
      return this.props.fallback ?? (
        <div className="flex flex-col items-center justify-center h-full p-8 text-center">
          <div className="w-12 h-12 rounded-xl bg-rose/10 flex items-center justify-center mb-4">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F43F5E" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <p className="text-sm font-medium text-white mb-1">Something went wrong</p>
          <p className="text-xs text-muted mb-4 max-w-sm">{this.state.error.message}</p>
          <button
            onClick={() => this.setState({ error: null })}
            className="btn-ghost text-xs"
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
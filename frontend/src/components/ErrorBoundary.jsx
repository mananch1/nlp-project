import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught a runtime error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    } else {
      window.location.reload();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-100 flex items-center justify-center p-6">
          <div className="max-w-lg w-full bg-white rounded-2xl shadow-lg border border-red-200 p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-red-100 text-red-600 rounded-xl">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900">Application Error Encountered</h2>
                <p className="text-xs text-slate-500">
                  A rendering error occurred while displaying the compliance audit data.
                </p>
              </div>
            </div>

            <div className="p-3 bg-red-50 rounded-lg border border-red-200 text-xs font-mono text-red-800 break-words">
              {this.state.error?.toString()}
            </div>

            {this.state.errorInfo?.componentStack && (
              <details className="text-xs text-slate-500 bg-slate-50 p-2.5 rounded border border-slate-200">
                <summary className="cursor-pointer font-semibold text-slate-700">View Component Trace</summary>
                <pre className="mt-2 whitespace-pre-wrap font-mono text-[11px] max-h-40 overflow-y-auto">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={this.handleReset}
                className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs px-4 py-2 rounded-lg transition-colors shadow-sm"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Reset Application</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

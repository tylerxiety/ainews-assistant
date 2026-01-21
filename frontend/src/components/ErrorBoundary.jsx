
import React from 'react';
import { Link } from 'react-router-dom';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        // Update state so the next render will show the fallback UI.
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        // You can also log the error to an error reporting service
        if (import.meta.env.DEV) {
            console.error("ErrorBoundary caught an error:", error, errorInfo);
        }
        this.setState({ errorInfo });
    }

    render() {
        if (this.state.hasError) {
            // Fallback UI
            return (
                <div style={{
                    padding: '2rem',
                    textAlign: 'center',
                    color: '#fff',
                    backgroundColor: '#1a1a1a',
                    minHeight: '100vh',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center'
                }}>
                    <h1>Something went wrong.</h1>
                    <p style={{ maxWidth: '600px', margin: '1rem 0' }}>
                        {this.state.error && this.state.error.toString()}
                    </p>
                    <div style={{ marginTop: '2rem' }}>
                        <button
                            onClick={() => window.location.reload()}
                            style={{
                                padding: '0.8rem 1.5rem',
                                backgroundColor: '#646cff',
                                color: 'white',
                                border: 'none',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                fontSize: '1rem',
                                marginRight: '1rem'
                            }}
                        >
                            Reload Page
                        </button>
                        <a href="/" style={{ color: '#646cff', textDecoration: 'none' }}>Go Home</a>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;

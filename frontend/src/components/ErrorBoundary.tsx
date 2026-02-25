import React, { Component, ReactNode } from "react";
import { ErrorPage } from "./ErrorPage";

interface Props {
    children: ReactNode;
    onGoHome: () => void;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    // Explicitly declare inherited properties to satisfy strict TS linter
    public state: State;
    public props: Props;
    // @ts-ignore
    public setState: (state: Partial<State> | ((prevState: State, props: Props) => Partial<State>)) => void;

    constructor(props: Props) {
        super(props);
        this.props = props;
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, info: React.ErrorInfo) {
        console.error("[Ripple ErrorBoundary]", error, info.componentStack);
    }

    handleRetry = () => {
        this.setState({ hasError: false, error: null });
    };

    render() {
        if (this.state.hasError) {
            return (
                <ErrorPage
                    error={this.state.error}
                    onRetry={this.handleRetry}
                    onGoHome={this.props.onGoHome}
                />
            );
        }
        return this.props.children;
    }
}
